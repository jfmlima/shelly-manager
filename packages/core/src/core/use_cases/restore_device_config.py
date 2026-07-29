"""Use case for restoring a stored backup back onto a device."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.generation import Generation
from core.domain.value_objects.restore_result import (
    ComponentRestoreResult,
    RestoreResult,
)
from core.gateways.device import DeviceGateway
from core.repositories.backup_repository import BackupRepository
from core.use_cases.backup_device_config import BackupNotFoundError
from core.use_cases.restore_strategies import (
    LEGACY_SETTINGS_KEY,
    ComponentRestoreStrategy,
)
from core.use_cases.restore_strategies.gen1 import Gen1RestoreStrategy
from core.use_cases.restore_strategies.gen2 import Gen2RestoreStrategy
from core.utils.validation import normalize_mac

logger = logging.getLogger(__name__)

# Component types that can drop the device off the network if restored.
# Excluded from the default selection; applied LAST when explicitly included.
NETWORK_TYPES = {"wifi", "eth", "mqtt", "ws", "cloud"}


class DeviceMismatchError(Exception):
    """Raised when the target device MAC does not match the backup."""

    def __init__(self, expected_mac: str, actual_mac: str | None):
        self.expected_mac = expected_mac
        self.actual_mac = actual_mac
        super().__init__(
            f"Device MAC mismatch: backup is for {expected_mac}, "
            f"target is {actual_mac or 'unknown'}"
        )


class RestoreDeviceConfig:
    """Apply a stored backup back to a device, per component key.

    Orchestration only: backup lookup, identity and generation checks,
    selection and ordering, result aggregation. The per-generation wire work
    lives in the restore strategies.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        repository_factory: Callable[[], AbstractAsyncContextManager[BackupRepository]],
        *,
        mode_change_timeout: float = 60.0,
        mode_change_poll_interval: float = 2.0,
    ):
        self._device_gateway = device_gateway
        self._repository_factory = repository_factory
        self._mode_change_timeout = mode_change_timeout
        self._mode_change_poll_interval = mode_change_poll_interval

    async def restore(
        self,
        backup_id: int,
        device_ip: str,
        *,
        component_keys: list[str] | None = None,
        allow_mac_mismatch: bool = False,
        reboot: bool = False,
    ) -> RestoreResult:
        """Restore selected components from a backup onto a device.

        Args:
            backup_id: ID of the backup to restore.
            device_ip: Target device IP address.
            component_keys: Explicit component keys to restore. When ``None``,
                restores every component except network types (wifi/eth/mqtt/
                ws/cloud), which are excluded by default to avoid lockout.
            allow_mac_mismatch: Restore even if the target MAC differs.
            reboot: Reboot the device after a successful restore.

        Raises:
            BackupNotFoundError: If the backup does not exist.
            DeviceNotFoundError: If the device is unreachable.
            DeviceMismatchError: If the MAC differs and the mismatch is not allowed.

        Note:
            Auth restore is out of scope for v1 (Gen2 auth is set via
            ``Shelly.SetAuth``, a separate RPC, not ``SetConfig``).
        """
        async with self._repository_factory() as repository:
            backup = await repository.get(backup_id)
        if backup is None:
            raise BackupNotFoundError(backup_id)

        status = await self._device_gateway.get_device_status(device_ip)
        if status is None:
            raise DeviceNotFoundError(device_ip)

        # Identity check is anchored to the MAC inside the (decrypted) snapshot,
        # not the mutable plaintext column. Cross-check the column for corruption.
        snapshot_info = backup.snapshot.get("device_info", {})
        snapshot_mac = snapshot_info.get("mac_address")
        expected_mac = (
            normalize_mac(snapshot_mac) if snapshot_mac else backup.device_mac
        )
        if snapshot_mac and normalize_mac(snapshot_mac) != backup.device_mac:
            logger.warning(
                "Backup %s metadata MAC (%s) != snapshot MAC (%s)",
                backup.id,
                backup.device_mac,
                normalize_mac(snapshot_mac),
            )

        if not allow_mac_mismatch:
            actual = normalize_mac(status.mac_address) if status.mac_address else None
            if actual != expected_mac:
                raise DeviceMismatchError(expected_mac, status.mac_address)

        components: dict[str, Any] = backup.snapshot.get("components", {})

        # A target whose generation is unknown (gen is None, e.g. GetDeviceInfo
        # failed) is already gated by the MAC check above, so it never reaches here.
        backup_generation = Generation.from_label(backup.generation)
        device_generation = Generation.from_device_gen(status.gen)
        is_gen1 = (
            backup_generation is Generation.GEN1
            and device_generation is Generation.GEN1
        )
        if (
            backup_generation is Generation.GEN1 or device_generation is Generation.GEN1
        ) and not is_gen1:
            return self._generation_mismatch(backup, device_ip, component_keys)

        strategy = self._build_strategy(Generation.GEN1 if is_gen1 else Generation.GEN2)
        outcome = await strategy.prepare(device_ip, backup, status)
        if outcome.abort_reason is not None:
            return self._all_skipped(
                backup, device_ip, component_keys, outcome.abort_reason
            )
        failure = next(
            (r for r in outcome.preliminary if not r.success and not r.skipped), None
        )
        if failure is not None:
            return RestoreResult(
                success=False,
                device_ip=device_ip,
                backup_id=backup_id,
                total=len(outcome.preliminary),
                succeeded=sum(1 for r in outcome.preliminary if r.success),
                failed=sum(
                    1 for r in outcome.preliminary if not r.success and not r.skipped
                ),
                skipped=sum(1 for r in outcome.preliminary if r.skipped),
                message=failure.error,
                components=outcome.preliminary,
            )

        status = outcome.status
        present_keys = {component.key for component in status.components}
        selected = self._select(components, component_keys)

        results: list[ComponentRestoreResult] = list(outcome.preliminary)
        # Surface explicitly-requested keys that aren't in the backup, so the
        # caller never silently gets a smaller restore set than they asked for.
        if component_keys is not None:
            for key in component_keys:
                if key == LEGACY_SETTINGS_KEY and key in components:
                    results.append(
                        ComponentRestoreResult(
                            key=key,
                            action="SetConfig",
                            success=False,
                            skipped=True,
                            skipped_reason="not a restorable component",
                        )
                    )
                elif key not in components:
                    results.append(
                        ComponentRestoreResult(
                            key=key,
                            action="SetConfig",
                            success=False,
                            skipped=True,
                            skipped_reason="not present in backup",
                        )
                    )
        for key in selected:
            results.append(
                await strategy.restore_component(
                    device_ip, key, components[key], present_keys
                )
            )

        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        # A restore only "succeeds" if something was actually applied. An
        # all-skipped restore (e.g. unknown keys, or every component absent on
        # the target) is a no-op, not a success, and must not reboot.
        applied = succeeded > 0 and failed == 0

        if reboot and applied:
            await strategy.reboot(device_ip)

        return RestoreResult(
            success=applied,
            device_ip=device_ip,
            backup_id=backup_id,
            total=len(results),
            succeeded=succeeded,
            failed=failed,
            skipped=skipped,
            message=(
                None
                if applied
                else "No components were applied" if failed == 0 else None
            ),
            components=results,
        )

    def _build_strategy(self, generation: Generation) -> ComponentRestoreStrategy:
        # Strategies are stateful per run (Gen1 holds the loaded settings), so
        # each restore constructs its own.
        if generation is Generation.GEN1:
            return Gen1RestoreStrategy(
                self._device_gateway,
                mode_change_timeout=self._mode_change_timeout,
                mode_change_poll_interval=self._mode_change_poll_interval,
            )
        return Gen2RestoreStrategy(self._device_gateway)

    def _select(
        self, components: dict[str, Any], component_keys: list[str] | None
    ) -> list[str]:
        """Resolve the ordered list of component keys to restore.

        Default (no explicit selection) excludes network types. Network keys are
        always ordered last so connectivity-risk components apply after the rest.
        """
        candidates = {
            key: entry
            for key, entry in components.items()
            if key != LEGACY_SETTINGS_KEY
        }
        if component_keys is None:
            keys = [
                key
                for key, entry in candidates.items()
                if entry.get("type") not in NETWORK_TYPES
            ]
        else:
            keys = [key for key in component_keys if key in candidates]

        def is_network(key: str) -> bool:
            return candidates[key].get("type") in NETWORK_TYPES

        return sorted(keys, key=is_network)

    def _generation_mismatch(
        self,
        backup: DeviceBackup,
        device_ip: str,
        component_keys: list[str] | None = None,
    ) -> RestoreResult:
        return self._all_skipped(
            backup,
            device_ip,
            component_keys,
            "backup generation does not match the target device",
            message="Backup and device generations differ",
        )

    def _all_skipped(
        self,
        backup: DeviceBackup,
        device_ip: str,
        component_keys: list[str] | None,
        reason: str,
        message: str | None = None,
    ) -> RestoreResult:
        components: dict[str, Any] = backup.snapshot.get("components", {})
        # Honour an explicit request subset, and still surface unknown keys
        # rather than reporting every captured component as skipped. The default
        # selection mirrors the restore path, so network components a default
        # restore would never touch are not reported as skipped either.
        keys = (
            self._select(components, None) if component_keys is None else component_keys
        )
        results = [
            ComponentRestoreResult(
                key=key,
                action="SetConfig",
                success=False,
                skipped=True,
                skipped_reason=(
                    reason if key in components else "not present in backup"
                ),
            )
            for key in keys
        ]
        return RestoreResult(
            success=False,
            device_ip=device_ip,
            backup_id=backup.id or 0,
            total=len(results),
            succeeded=0,
            failed=0,
            skipped=len(results),
            message=message or reason,
            components=results,
        )
