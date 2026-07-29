import asyncio
from datetime import UTC, datetime
from typing import Any

from ..domain.entities.config_snapshot import DeviceSnapshot
from ..domain.entities.exceptions import BulkOperationError
from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway
from .capture_device_config import CaptureDeviceConfig


class BulkOperationsUseCase:

    def __init__(
        self,
        device_gateway: DeviceGateway,
    ):
        self._device_gateway = device_gateway
        self._capture = CaptureDeviceConfig(device_gateway)

    async def execute_bulk_update(
        self, device_ips: list[str], channel: str = "stable"
    ) -> list[ActionResult]:
        """
        Update firmware on multiple devices.

        Args:
            device_ips: List of device IP addresses
            channel: Update channel (stable/beta)

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "Update", {"channel": channel}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_update", device_ips, f"Bulk update failed: {str(e)}"
            ) from e

    async def execute_bulk_reboot(self, device_ips: list[str]) -> list[ActionResult]:
        """
        Reboot multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "Reboot", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_reboot", device_ips, f"Bulk reboot failed: {str(e)}"
            ) from e

    async def execute_bulk_factory_reset(
        self, device_ips: list[str]
    ) -> list[ActionResult]:
        """
        Factory reset multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", "FactoryReset", {}
            )
        except Exception as e:
            raise BulkOperationError(
                "bulk_factory_reset", device_ips, f"Bulk factory reset failed: {str(e)}"
            ) from e

    async def export_bulk_config(
        self,
        device_ips: list[str],
        component_types: list[str],
    ) -> dict[str, Any]:
        """
        Export component configurations organized per device.

        Unreachable devices are left out of the export rather than failing it.

        Args:
            device_ips: List of device IP addresses
            component_types: List of component types to export

        Returns:
            Dictionary containing export metadata and device configurations
        """
        snapshots = await self._capture_all(device_ips, component_types)

        return {
            "export_metadata": {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "total_devices": len(device_ips),
                "component_types": component_types,
            },
            "devices": {
                device_ip: snapshot.to_dict()
                for device_ip, snapshot in zip(device_ips, snapshots, strict=False)
                if snapshot is not None
            },
        }

    async def _capture_all(
        self, device_ips: list[str], component_types: list[str]
    ) -> list[DeviceSnapshot | None]:
        """Capture every device concurrently, in the order they were asked for.

        Gathering with ``return_exceptions`` lets every capture finish before a
        failure surfaces, so one bad device does not leave the others running
        against real hardware with nobody awaiting them.
        """
        results = await asyncio.gather(
            *(self._capture_device(ip, component_types) for ip in device_ips),
            return_exceptions=True,
        )
        snapshots: list[DeviceSnapshot | None] = []
        for result in results:
            if isinstance(result, BaseException):
                raise result
            snapshots.append(result)
        return snapshots

    async def _capture_device(
        self, device_ip: str, component_types: list[str]
    ) -> DeviceSnapshot | None:
        status = await self._device_gateway.get_device_status(device_ip)
        if not status:
            return None
        return await self._capture.capture(device_ip, status, component_types)

    async def apply_bulk_config(
        self,
        device_ips: list[str],
        component_type: str,
        config: dict[str, Any],
    ) -> list[ActionResult]:
        """
        Apply component configuration to multiple devices.

        Resolves actual component keys (e.g. cover:0) per device to ensure
        the RPC call includes the required component ID.

        Args:
            device_ips: List of device IP addresses
            component_type: Type of component to apply configuration to
            config: Configuration to apply

        Returns:
            List of action results
        """
        all_results = []

        for device_ip in device_ips:
            keys = await self._device_gateway.get_component_keys(
                device_ip, component_type
            )

            if not keys:
                all_results.append(
                    ActionResult(
                        device_ip=device_ip,
                        action_type=f"{component_type}.SetConfig",
                        success=False,
                        message=f"No {component_type} components found on device",
                        error=f"Component type {component_type} not present"
                        " or device unreachable",
                    )
                )
                continue

            for key in keys:
                result = await self._device_gateway.execute_component_action(
                    device_ip, key, "SetConfig", {"config": config}
                )
                all_results.append(result)

        return all_results
