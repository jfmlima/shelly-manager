"""Restore strategy for Gen1 (legacy HTTP) devices.

Gen1 restores replay the raw ``/settings`` captured at backup time; the mapped
per-component configs are Gen2-shaped and not writable as-is.
"""

import asyncio
from typing import Any

from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.device_status import DeviceStatus
from core.domain.services.gen1_settings_translation import (
    restorable_params,
    wifi_subresources,
)
from core.domain.value_objects.restore_result import ComponentRestoreResult
from core.gateways.device import DeviceGateway
from core.use_cases.restore_strategies import LEGACY_SETTINGS_KEY, PrepareOutcome


class Gen1RestoreStrategy:
    """Replay a raw Gen1 /settings snapshot over the legacy HTTP endpoints.

    Stateful per restore run: ``prepare`` loads the raw settings the component
    loop replays, so one instance serves exactly one restore.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        *,
        mode_change_timeout: float = 60.0,
        mode_change_poll_interval: float = 2.0,
    ):
        self._device_gateway = device_gateway
        self._mode_change_timeout = mode_change_timeout
        self._mode_change_poll_interval = mode_change_poll_interval
        self._settings: dict[str, Any] = {}

    async def prepare(
        self, device_ip: str, backup: DeviceBackup, status: DeviceStatus
    ) -> PrepareOutcome:
        settings = self._legacy_settings(backup)
        if settings is None:
            return PrepareOutcome(
                status=status, abort_reason="snapshot lacks raw Gen1 settings"
            )
        self._settings = settings

        mode_result, status = await self._sync_mode(device_ip, settings, status)
        return PrepareOutcome(
            status=status,
            preliminary=[mode_result] if mode_result is not None else [],
        )

    async def restore_component(
        self,
        device_ip: str,
        key: str,
        entry: dict[str, Any],
        present_keys: set[str],
    ) -> ComponentRestoreResult:
        ctype = entry.get("type")

        if key not in present_keys:
            return ComponentRestoreResult(
                key=key,
                action="Legacy.SetConfig",
                success=False,
                skipped=True,
                skipped_reason="component not present on target device",
            )

        if ctype == "wifi":
            return await self._restore_wifi(device_ip, key)

        params = restorable_params(key, ctype, self._settings)
        if params is None:
            return ComponentRestoreResult(
                key=key,
                action="Legacy.SetConfig",
                success=False,
                skipped=True,
                skipped_reason="no Gen1 settings endpoint for this component",
            )
        if not params:
            return ComponentRestoreResult(
                key=key,
                action="Legacy.SetConfig",
                success=False,
                skipped=True,
                skipped_reason="no restorable settings captured in backup",
            )

        result = await self._device_gateway.execute_component_action(
            device_ip, key, "Legacy.SetConfig", params
        )
        return ComponentRestoreResult(
            key=key,
            action="Legacy.SetConfig",
            success=result.success,
            error=result.error if not result.success else None,
        )

    async def reboot(self, device_ip: str) -> None:
        await self._device_gateway.execute_component_action(
            device_ip, "sys", "Legacy.Reboot", {}
        )

    def _legacy_settings(self, backup: DeviceBackup) -> dict[str, Any] | None:
        components: dict[str, Any] = backup.snapshot.get("components", {})
        entry = components.get(LEGACY_SETTINGS_KEY)
        if not isinstance(entry, dict) or not entry.get("success"):
            return None
        settings = entry.get("config")
        return settings if isinstance(settings, dict) else None

    async def _restore_wifi(self, device_ip: str, key: str) -> ComponentRestoreResult:
        """Replay every captured Gen1 WiFi resource behind the "wifi" component."""
        subresources = wifi_subresources(self._settings)
        errors: list[str] = []
        for subtype, params in subresources:
            result = await self._device_gateway.execute_component_action(
                device_ip, subtype, "Legacy.SetConfig", params
            )
            if not result.success:
                errors.append(f"{subtype}: {result.error or 'failed'}")

        if not subresources:
            return ComponentRestoreResult(
                key=key,
                action="Legacy.SetConfig",
                success=False,
                skipped=True,
                skipped_reason="no restorable settings captured in backup",
            )
        return ComponentRestoreResult(
            key=key,
            action="Legacy.SetConfig",
            success=not errors,
            error="; ".join(errors) if errors else None,
        )

    async def _sync_mode(
        self,
        device_ip: str,
        settings: dict[str, Any],
        status: DeviceStatus,
    ) -> tuple[ComponentRestoreResult | None, DeviceStatus]:
        """Align the target's relay/roller mode with the backup before restoring.

        Gen1 applies ``mode`` with a reboot and re-enumerates its components
        afterwards, so it cannot ride along in the sys param batch: it is sent
        alone first, and the device status is re-read once the target is back.
        Returns the pre-phase result (``None`` when nothing needed doing) and
        the status to restore against.
        """
        backup_mode = settings.get("mode")
        if not isinstance(backup_mode, str) or not backup_mode:
            return None, status

        target_settings = await self._device_gateway.get_legacy_settings(device_ip)
        target_mode = (
            target_settings.get("mode") if isinstance(target_settings, dict) else None
        )
        if not isinstance(target_mode, str) or not target_mode:
            return (
                ComponentRestoreResult(
                    key="mode",
                    action="Legacy.SetConfig",
                    success=False,
                    skipped=True,
                    skipped_reason="could not read the target device mode",
                ),
                status,
            )
        if target_mode == backup_mode:
            return None, status

        result = await self._device_gateway.execute_component_action(
            device_ip, "sys", "Legacy.SetConfig", {"mode": backup_mode}
        )
        if not result.success:
            return (
                ComponentRestoreResult(
                    key="mode",
                    action="Legacy.SetConfig",
                    success=False,
                    error=result.error or "mode change failed",
                ),
                status,
            )

        new_status = await self._wait_for_device(device_ip)
        if new_status is None:
            return (
                ComponentRestoreResult(
                    key="mode",
                    action="Legacy.SetConfig",
                    success=False,
                    error="device did not come back after the mode change",
                ),
                status,
            )
        return (
            ComponentRestoreResult(key="mode", action="Legacy.SetConfig", success=True),
            new_status,
        )

    async def _wait_for_device(self, device_ip: str) -> DeviceStatus | None:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + self._mode_change_timeout
        while True:
            status = await self._device_gateway.get_device_status(device_ip)
            if status is not None:
                return status
            if loop.time() >= deadline:
                return None
            await asyncio.sleep(self._mode_change_poll_interval)
