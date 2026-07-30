import asyncio
from datetime import UTC, datetime
from typing import Any

from ..domain.entities.config_snapshot import DeviceSnapshot
from ..domain.entities.exceptions import BulkOperationError
from ..domain.value_objects.action_result import ActionResult
from ..gateways.device import DeviceGateway
from .capture_device_config import CaptureDeviceConfig


def _unique(device_ips: list[str]) -> list[str]:
    """The given IPs in order, without repeats.

    Overlapping targets ("-t 10.0.0.5 -t 10.0.0.0/24") expand to the same device
    more than once. Handling devices concurrently would then put two overlapping
    requests on one device, which is the thing the per-device sequencing exists
    to avoid.
    """
    return list(dict.fromkeys(device_ips))


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
        return await self._execute_shelly_action(
            device_ips, "Update", {"channel": channel}, "bulk_update", "Bulk update"
        )

    async def execute_bulk_reboot(self, device_ips: list[str]) -> list[ActionResult]:
        """
        Reboot multiple devices.

        Args:
            device_ips: List of device IP addresses

        Returns:
            List of action results
        """
        return await self._execute_shelly_action(
            device_ips, "Reboot", {}, "bulk_reboot", "Bulk reboot"
        )

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
        return await self._execute_shelly_action(
            device_ips, "FactoryReset", {}, "bulk_factory_reset", "Bulk factory reset"
        )

    async def _execute_shelly_action(
        self,
        device_ips: list[str],
        action: str,
        parameters: dict[str, Any],
        operation: str,
        label: str,
    ) -> list[ActionResult]:
        """Run one action on the shelly component of every device.

        ``operation`` and ``label`` only shape the error a failure raises.
        """
        try:
            return await self._device_gateway.execute_bulk_action(
                device_ips, "shelly", action, parameters
            )
        except Exception as e:
            raise BulkOperationError(
                operation, device_ips, f"{label} failed: {str(e)}"
            ) from e

    async def export_bulk_config(
        self,
        device_ips: list[str],
        component_types: list[str],
    ) -> dict[str, Any]:
        """
        Export component configurations organized per device.

        Devices are captured concurrently, each at most once. Unreachable
        devices are left out of the export rather than failing it.

        Args:
            device_ips: List of device IP addresses
            component_types: List of component types to export

        Returns:
            Dictionary containing export metadata and device configurations
        """
        targets = _unique(device_ips)
        snapshots = await self._capture_all(targets, component_types)

        return {
            "export_metadata": {
                "timestamp": datetime.now(UTC).isoformat() + "Z",
                "total_devices": len(targets),
                "component_types": component_types,
            },
            "devices": {
                device_ip: snapshot.to_dict()
                for device_ip, snapshot in zip(targets, snapshots, strict=True)
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

        Devices are handled concurrently and each is configured at most once;
        the components of a single device are configured one at a time. Results
        stay in device order.

        Resolves actual component keys (e.g. cover:0) per device to ensure
        the RPC call includes the required component ID.

        Args:
            device_ips: List of device IP addresses
            component_type: Type of component to apply configuration to
            config: Configuration to apply

        Returns:
            List of action results
        """
        per_device = await asyncio.gather(
            *(
                self._apply_device_config(device_ip, component_type, config)
                for device_ip in _unique(device_ips)
            )
        )
        return [result for results in per_device for result in results]

    async def _apply_device_config(
        self,
        device_ip: str,
        component_type: str,
        config: dict[str, Any],
    ) -> list[ActionResult]:
        keys = await self._device_gateway.get_component_keys(device_ip, component_type)

        if not keys:
            return [
                ActionResult(
                    device_ip=device_ip,
                    action_type=f"{component_type}.SetConfig",
                    success=False,
                    message=f"No {component_type} components found on device",
                    error=f"Component type {component_type} not present"
                    " or device unreachable",
                )
            ]

        return [
            await self._device_gateway.execute_component_action(
                device_ip, key, "SetConfig", {"config": config}
            )
            for key in keys
        ]
