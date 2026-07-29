"""Restore strategy for Gen2+ (RPC) devices."""

from copy import deepcopy
from typing import Any

from core.domain.entities.device_backup import DeviceBackup
from core.domain.entities.device_status import DeviceStatus
from core.domain.value_objects.restore_result import ComponentRestoreResult
from core.gateways.device import DeviceGateway
from core.use_cases.restore_strategies import PrepareOutcome

# The "schedules" pseudo-component produced by export_bulk_config.
SCHEDULES_KEY = "schedules"

# Read-only keys that GetConfig echoes but SetConfig rejects, by component type.
# Each entry is a (parent, child) path popped from the config dict. Top-level
# "id" and "cfg_rev" are always stripped. Table-driven so it is easy to extend.
READ_ONLY_BY_TYPE: dict[str, list[tuple[str, str]]] = {
    "sys": [("device", "mac")],
    "wifi": [("ap", "is_open")],
}


class Gen2RestoreStrategy:
    """Apply captured component configs over the Gen2+ RPC surface."""

    def __init__(self, device_gateway: DeviceGateway):
        self._device_gateway = device_gateway

    async def prepare(
        self, device_ip: str, backup: DeviceBackup, status: DeviceStatus
    ) -> PrepareOutcome:
        return PrepareOutcome(status=status)

    async def restore_component(
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

    async def reboot(self, device_ip: str) -> None:
        await self._device_gateway.execute_component_action(
            device_ip, "shelly", "Reboot", {}
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
        # the captured set is empty). If the clear fails, abort: creating on top
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
