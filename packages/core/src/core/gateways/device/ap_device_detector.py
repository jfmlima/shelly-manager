"""Detects and identifies Shelly devices via their AP at a given IP."""

import logging
from typing import Any

import httpx

from core.domain.entities.exceptions import (
    DeviceCommunicationError,
    DeviceNotFoundError,
)
from core.domain.value_objects.provision_request import APDeviceInfo

logger = logging.getLogger(__name__)


class APDeviceDetector:
    """Detects a Shelly device in AP mode via GET /shelly.

    This endpoint is always unauthenticated, even when auth is enabled.
    """

    def __init__(self, timeout: float = 5.0) -> None:
        self._timeout = timeout

    async def detect(self, ip: str, timeout: float | None = None) -> APDeviceInfo:
        """Detect a Shelly device at the given IP address.

        Args:
            ip: IP address of the device (typically 192.168.33.1 in AP mode).
            timeout: Optional timeout override.

        Returns:
            APDeviceInfo with device identification data.

        Raises:
            DeviceNotFoundError: If the device is not reachable or not a Shelly.
            DeviceCommunicationError: On network errors.
        """
        effective_timeout = timeout or self._timeout
        url = f"http://{ip}/shelly"

        try:
            async with httpx.AsyncClient(timeout=effective_timeout) as client:
                response = await client.get(url)
        except httpx.TimeoutException as exc:
            raise DeviceNotFoundError(
                ip, f"Device at {ip} did not respond within {effective_timeout}s"
            ) from exc
        except httpx.RequestError as e:
            raise DeviceCommunicationError(
                ip, str(e), f"Failed to connect to device at {ip}"
            ) from e

        if response.status_code != 200:
            raise DeviceCommunicationError(
                ip,
                f"HTTP {response.status_code}",
                f"Unexpected response from {ip}",
            )

        try:
            data: dict[str, Any] = response.json()
        except Exception as e:
            raise DeviceCommunicationError(
                ip, str(e), f"Invalid JSON response from {ip}"
            ) from e

        return self._parse_device_info(ip, data)

    def _parse_device_info(self, ip: str, data: dict[str, Any]) -> APDeviceInfo:
        """Parse the /shelly response into APDeviceInfo.

        Gen2+ devices have a 'gen' field (2 or 3).
        Gen1 devices have a 'type' field but no 'gen' field.
        """
        generation = data.get("gen")

        if generation is None:
            # This is a Gen1 device
            device_type = data.get("type", "")
            if not device_type:
                raise DeviceNotFoundError(
                    ip, f"Device at {ip} does not appear to be a Shelly device"
                )
            raise DeviceNotFoundError(
                ip,
                f"Device at {ip} is a Gen1 Shelly ({device_type}). "
                "Only Gen2/Gen3 devices are supported for provisioning.",
            )

        # Gen2/Gen3 device
        device_id = data.get("id", "")
        mac = data.get("mac", "")
        model = data.get("model", "")
        fw_id = data.get("fw_id", "")
        ver = data.get("ver", fw_id)
        auth_enabled = data.get("auth_en", False)
        auth_domain = data.get("auth_domain")
        app = data.get("app")

        if not device_id or not mac:
            raise DeviceNotFoundError(
                ip,
                f"Device at {ip} returned incomplete identification data",
            )

        logger.info(
            "Detected %s device: id=%s, model=%s, gen=%d, auth=%s",
            app or model,
            device_id,
            model,
            generation,
            auth_enabled,
        )

        return APDeviceInfo(
            device_id=device_id,
            mac=mac.upper().replace(":", ""),
            model=model,
            generation=generation,
            firmware_version=ver,
            auth_enabled=auth_enabled,
            auth_domain=auth_domain or device_id,
            app=app,
        )
