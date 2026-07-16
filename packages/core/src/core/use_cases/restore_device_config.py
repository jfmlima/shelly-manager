"""Use case for restoring a stored backup back onto a device."""

import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from copy import deepcopy
from typing import Any

from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.exceptions import DeviceNotFoundError
from core.domain.value_objects.restore_result import (
    ComponentRestoreResult,
    RestoreResult,
)
from core.gateways.device import DeviceGateway
from core.repositories.backup_repository import BackupRepository
from core.use_cases.backup_device_config import BackupNotFoundError
from core.utils.validation import normalize_mac

logger = logging.getLogger(__name__)

# Component types that can drop the device off the network if restored.
# Excluded from the default selection; applied LAST when explicitly included.
NETWORK_TYPES = {"wifi", "eth", "mqtt", "ws", "cloud"}

# The "schedules" pseudo-component produced by export_bulk_config.
SCHEDULES_KEY = "schedules"

# The raw Gen1 /settings entry captured alongside the mapped components. It is the
# data source a Gen1 restore replays, never a restore target itself.
LEGACY_SETTINGS_KEY = "legacy_settings"

# Section of the raw /settings holding each component's config. "" is the top level.
GEN1_SECTION_BY_TYPE: dict[str, str] = {
    "switch": "relays",
    "cover": "rollers",
    "sys": "",
    "mqtt": "mqtt",
    "cloud": "cloud",
    "wifi": "wifi_sta",
}

# Restorable Gen1 settings per component type, as GET /settings names them. Only
# params documented as settable at https://shelly-api-docs.shelly.cloud/gen1/ are
# listed, so read-only echoes (ison, has_timer, power, is_valid, safety_switch) are
# never sent back. Fields a model does not have are absent and skip themselves,
# which is what lets one table serve every Gen1 model.
GEN1_RESTORABLE_BY_TYPE: dict[str, tuple[str, ...]] = {
    "switch": (
        "name",
        "appliance_type",
        "default_state",
        "btn_type",
        "btn_reverse",
        # Shelly 1L exposes two inputs instead of one.
        "btn1_type",
        "btn1_reverse",
        "btn2_type",
        "btn2_reverse",
        "swap_inputs",
        "auto_on",
        "auto_off",
        "schedule",
        "schedule_rules",
        "max_power",
    ),
    "cover": (
        "default_state",
        "input_mode",
        "button_type",
        "btn_reverse",
        "swap",
        "swap_inputs",
        "maxtime",
        "maxtime_open",
        "maxtime_close",
        "positioning",
        "obstacle_mode",
        "obstacle_action",
        "obstacle_power",
        "obstacle_delay",
        "ends_delay",
        "off_power",
        "safety_mode",
        "safety_action",
        "safety_allowed_on_trigger",
        "schedule",
        "schedule_rules",
    ),
    "sys": (
        "name",
        "timezone",
        "tzautodetect",
        "tz_utc_offset",
        "tz_dst",
        "tz_dst_auto",
        "lat",
        "lng",
        "discoverable",
        "led_status_disable",
        "sntp.server",
    ),
    # mqtt_pass is not echoed by GET /settings, so it cannot be restored.
    "mqtt": (
        "enable",
        "server",
        "user",
        "id",
        "clean_session",
        "retain",
        "keep_alive",
        "update_period",
        "max_qos",
        "reconnect_timeout_min",
        "reconnect_timeout_max",
    ),
    "cloud": ("enabled",),
    # The WiFi "key" is not echoed by GET /settings, so it cannot be restored.
    "wifi": ("enabled", "ssid", "ipv4_method", "ip", "gw", "mask", "dns"),
}

# GET /settings echoes several fields under a different name than the one their
# setter accepts; sending the echoed name is silently ignored by the device.
GEN1_PARAM_RENAMES: dict[str, dict[str, str]] = {
    "cover": {"button_type": "btn_type"},
    "sys": {"sntp.server": "sntp_server"},
    "mqtt": {name: f"mqtt_{name}" for name in GEN1_RESTORABLE_BY_TYPE["mqtt"]},
    "wifi": {"gw": "gateway", "mask": "netmask"},
}

# Read-only keys that GetConfig echoes but SetConfig rejects, by component type.
# Each entry is a (parent, child) path popped from the config dict. Top-level
# "id" and "cfg_rev" are always stripped. Table-driven so it is easy to extend.
READ_ONLY_BY_TYPE: dict[str, list[tuple[str, str]]] = {
    "sys": [("device", "mac")],
    "wifi": [("ap", "is_open")],
}


def _dig(section: dict[str, Any], path: str) -> Any:
    value: Any = section
    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


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
    """Apply a stored backup back to a device, per component key."""

    def __init__(
        self,
        device_gateway: DeviceGateway,
        repository_factory: Callable[[], AbstractAsyncContextManager[BackupRepository]],
    ):
        self._device_gateway = device_gateway
        self._repository_factory = repository_factory

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
        is_gen1 = backup.generation == "gen1" and status.gen == 1
        gen1_settings: dict[str, Any] | None = None
        if backup.generation == "gen1" or status.gen == 1:
            if not is_gen1:
                return self._generation_mismatch(backup, device_ip, component_keys)
            # Gen1 restores replay the raw /settings captured at backup time; the
            # mapped per-component configs are Gen2-shaped and not writable as-is.
            gen1_settings = self._legacy_settings(backup)
            if gen1_settings is None:
                return self._all_skipped(
                    backup,
                    device_ip,
                    component_keys,
                    "snapshot lacks raw Gen1 settings",
                )

        present_keys = {component.key for component in status.components}
        selected = self._select(components, component_keys)

        results: list[ComponentRestoreResult] = []
        # Surface explicitly-requested keys that aren't in the backup, so the
        # caller never silently gets a smaller restore set than they asked for.
        if component_keys is not None:
            for key in component_keys:
                if key == LEGACY_SETTINGS_KEY:
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
            entry = components[key]
            if gen1_settings is not None:
                results.append(
                    await self._restore_gen1_one(
                        device_ip, key, entry, gen1_settings, present_keys
                    )
                )
            else:
                results.append(
                    await self._restore_one(device_ip, key, entry, present_keys)
                )

        succeeded = sum(1 for r in results if r.success)
        failed = sum(1 for r in results if not r.success and not r.skipped)
        skipped = sum(1 for r in results if r.skipped)

        # A restore only "succeeds" if something was actually applied. An
        # all-skipped restore (e.g. unknown keys, or every component absent on
        # the target) is a no-op, not a success — and must not reboot.
        applied = succeeded > 0 and failed == 0

        if reboot and applied:
            if is_gen1:
                await self._device_gateway.execute_component_action(
                    device_ip, "sys", "Legacy.Reboot", {}
                )
            else:
                await self._device_gateway.execute_component_action(
                    device_ip, "shelly", "Reboot", {}
                )

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

    async def _restore_one(
        self,
        device_ip: str,
        key: str,
        entry: dict[str, Any],
        present_keys: set[str],
    ) -> ComponentRestoreResult:
        ctype = entry.get("type")

        if key == SCHEDULES_KEY:
            return await self._restore_schedules(device_ip, key, entry)
        if ctype == "script":
            return await self._restore_script(device_ip, key, entry, present_keys)

        if not entry.get("success") or entry.get("config") is None:
            return ComponentRestoreResult(
                key=key,
                action="SetConfig",
                success=False,
                skipped=True,
                skipped_reason="no config captured in backup",
            )
        if key not in present_keys:
            return ComponentRestoreResult(
                key=key,
                action="SetConfig",
                success=False,
                skipped=True,
                skipped_reason="component not present on target device",
            )

        config = self._strip_readonly(ctype, deepcopy(entry["config"]))
        result = await self._device_gateway.execute_component_action(
            device_ip, key, "SetConfig", {"config": config}
        )
        return ComponentRestoreResult(
            key=key,
            action="SetConfig",
            success=result.success,
            error=result.error if not result.success else None,
        )

    def _strip_readonly(
        self, ctype: str | None, config: dict[str, Any]
    ) -> dict[str, Any]:
        config.pop("id", None)
        config.pop("cfg_rev", None)
        for parent, child in READ_ONLY_BY_TYPE.get(ctype or "", []):
            section = config.get(parent)
            if isinstance(section, dict):
                section.pop(child, None)
        return config

    async def _restore_script(
        self,
        device_ip: str,
        key: str,
        entry: dict[str, Any],
        present_keys: set[str],
    ) -> ComponentRestoreResult:
        code_block = entry.get("code") or {}
        code = code_block.get("data") if isinstance(code_block, dict) else None
        # Presence + type, not truthiness: an empty script body ("") is valid.
        if not isinstance(code, str):
            return ComponentRestoreResult(
                key=key,
                action="PutCode",
                success=False,
                skipped=True,
                skipped_reason="no script code captured in backup",
            )
        if key not in present_keys:
            return ComponentRestoreResult(
                key=key,
                action="PutCode",
                success=False,
                skipped=True,
                skipped_reason="script not present on target device",
            )
        try:
            script_id = int(key.split(":")[1])
        except (ValueError, IndexError):
            return ComponentRestoreResult(
                key=key,
                action="PutCode",
                success=False,
                skipped=True,
                skipped_reason="could not resolve script id",
            )

        result = await self._device_gateway.execute_component_action(
            device_ip, key, "PutCode", {"id": script_id, "code": code, "append": False}
        )
        return ComponentRestoreResult(
            key=key,
            action="PutCode",
            success=result.success,
            error=result.error if not result.success else None,
        )

    async def _restore_schedules(
        self, device_ip: str, key: str, entry: dict[str, Any]
    ) -> ComponentRestoreResult:
        # Gate on whether the schedules component was *captured*, not on job
        # count: a device with zero schedules is captured as {"jobs": []}, and
        # restoring it must still clear the target's schedules.
        if not entry.get("success") or entry.get("config") is None:
            return ComponentRestoreResult(
                key=key,
                action="Schedule.Replace",
                success=False,
                skipped=True,
                skipped_reason="no schedules captured in backup",
            )

        config = entry["config"]
        jobs = config.get("jobs", []) if isinstance(config, dict) else []

        # Restore must reproduce the captured schedule set, not merge into the
        # device's existing jobs. Always clear the target first so re-runs are
        # idempotent and stale/duplicate jobs don't accumulate (including when
        # the captured set is empty). If the clear fails, abort — creating on top
        # of un-cleared jobs would merge/duplicate instead of replace.
        delete_result = await self._device_gateway.execute_component_action(
            device_ip, "schedule", "DeleteAll", {}
        )
        if not delete_result.success:
            return ComponentRestoreResult(
                key=key,
                action="Schedule.Replace",
                success=False,
                error=f"DeleteAll failed: {delete_result.error or 'unknown error'}",
            )

        errors: list[str] = []
        for job in jobs:
            params = {k: v for k, v in job.items() if k != "id"}
            result = await self._device_gateway.execute_component_action(
                device_ip, "schedule", "Create", params
            )
            if not result.success:
                errors.append(result.error or "Schedule.Create failed")

        return ComponentRestoreResult(
            key=key,
            action="Schedule.Replace",
            success=not errors,
            error="; ".join(errors) if errors else None,
        )

    def _legacy_settings(self, backup: DeviceBackup) -> dict[str, Any] | None:
        components: dict[str, Any] = backup.snapshot.get("components", {})
        entry = components.get(LEGACY_SETTINGS_KEY)
        if not isinstance(entry, dict) or not entry.get("success"):
            return None
        settings = entry.get("config")
        return settings if isinstance(settings, dict) else None

    async def _restore_gen1_one(
        self,
        device_ip: str,
        key: str,
        entry: dict[str, Any],
        settings: dict[str, Any],
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

        params = self._gen1_params(key, ctype, settings)
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

    def _gen1_params(
        self, key: str, ctype: str | None, settings: dict[str, Any]
    ) -> dict[str, Any] | None:
        """``None`` when the type has no Gen1 settings endpoint at all (e.g. inputs,
        whose config lives on the owning relay); ``{}`` when it has one but the
        snapshot holds nothing to send.
        """
        allowed = GEN1_RESTORABLE_BY_TYPE.get(ctype or "")
        if allowed is None:
            return None

        section = self._gen1_section(key, ctype or "", settings)
        if section is None:
            return {}

        renames = GEN1_PARAM_RENAMES.get(ctype or "", {})
        params: dict[str, Any] = {}
        for attr in allowed:
            value = _dig(section, attr)
            if value is not None:
                params[renames.get(attr, attr)] = value
        return params

    def _gen1_section(
        self, key: str, ctype: str, settings: dict[str, Any]
    ) -> dict[str, Any] | None:
        section_name = GEN1_SECTION_BY_TYPE[ctype]
        section: Any = settings if not section_name else settings.get(section_name)

        # relays/rollers are arrays parallel to the component id.
        if isinstance(section, list):
            try:
                index = int(key.split(":")[1])
            except (IndexError, ValueError):
                return None
            section = section[index] if 0 <= index < len(section) else None

        return section if isinstance(section, dict) else None

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
        # rather than reporting every captured component as skipped.
        keys = (
            [key for key in components if key != LEGACY_SETTINGS_KEY]
            if component_keys is None
            else component_keys
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
