"""Use case for updating a device from the local firmware store."""

import logging
import re

from core.domain.entities.exceptions import (
    DeviceNotFoundError,
    FirmwareConfigurationError,
    FirmwareError,
)
from core.domain.value_objects.action_result import ActionResult
from core.domain.value_objects.base_device_request import BaseDeviceRequest
from core.gateways.device import DeviceGateway
from core.gateways.firmware import FirmwareGateway
from core.settings import FirmwareSettings
from core.use_cases.acquire_firmware import AcquireFirmware

logger = logging.getLogger(__name__)

# Changelog: "1.3.3 is a mandatory update before 1.4.0."
_MANDATORY_STEPS = (((1, 3, 3), (1, 4, 0)),)


class UpdateDeviceFromLocal:
    """Update a Gen2+ device with firmware served from the manager host.

    The device fetches the bundle over LAN from this API's firmware download
    route, so the device itself needs no internet access.
    """

    def __init__(
        self,
        device_gateway: DeviceGateway,
        firmware_gateway: FirmwareGateway,
        acquire_firmware: AcquireFirmware,
        settings: FirmwareSettings,
    ):
        self._device_gateway = device_gateway
        self._firmware_gateway = firmware_gateway
        self._acquire_firmware = acquire_firmware
        self._settings = settings

    async def execute(
        self, request: BaseDeviceRequest, channel: str = "stable"
    ) -> ActionResult:
        """Point the device at a locally cached copy of its latest firmware.

        Raises:
            DeviceNotFoundError: If the device is unreachable.
            FirmwareError: If the advertised base URL is unset, the device is
                Gen1 or reports no app name, no release is published on the
                channel, or a mandatory intermediate update is missing.
        """
        base_url = (self._settings.advertised_base_url or "").strip()
        if not base_url:
            raise FirmwareConfigurationError(
                "Local updates need SHELLY_FIRMWARE_ADVERTISED_BASE_URL set to "
                "a base URL devices can reach, e.g. http://192.168.40.252:8000"
            )

        ip = request.device_ip
        status = await self._device_gateway.get_device_status(ip)
        if status is None:
            raise DeviceNotFoundError(ip)

        if status.gen == 1:
            raise FirmwareError(
                f"Local updates support Gen2+ devices only; {ip} is Gen1",
                {"device_ip": ip},
            )

        if not status.app_name:
            raise FirmwareError(
                f"Device {ip} did not report an app name to look firmware up by",
                {"device_ip": ip},
            )

        release = await self._firmware_gateway.get_latest(status.app_name, channel)
        if release is None:
            raise FirmwareError(
                f"No {channel} firmware published for app '{status.app_name}'",
                {"app_name": status.app_name, "channel": channel},
            )

        installed = _installed_version(status.firmware_version)
        if release.is_installed_on(status.firmware_version):
            return ActionResult(
                device_ip=ip,
                action_type="shelly.Update",
                success=True,
                message=(
                    f"Device already runs the latest firmware ({release.version})"
                ),
            )

        step = _blocking_step(installed, release.version)
        if step is not None:
            raise FirmwareError(
                f"Device {ip} runs {installed}; Shelly requires {step} before"
                f" {release.version} can install. Update once with internet"
                f" access, then local updates work.",
                {"device_ip": ip, "installed": installed, "target": release.version},
            )

        downgrade = _downgrade_note(installed, release.version)
        if downgrade is not None:
            logger.warning("Local update for %s is a %s", ip, downgrade)

        bundle = await self._acquire_firmware.execute(status.app_name, release)
        url = f"{base_url.rstrip('/')}/api/firmware/{bundle.id}/download"
        logger.info(
            "Updating %s to %s %s from local bundle %s",
            ip,
            bundle.app_name,
            bundle.version,
            url,
        )
        result = await self._device_gateway.execute_component_action(
            ip, "shelly", "Update", {"url": url}
        )
        if downgrade is None:
            return result
        return result.model_copy(
            update={"message": f"{result.message} (this is a {downgrade})"}
        )


def _installed_version(firmware_version: str | None) -> str | None:
    """Version a device reports running.

    Reads the version out of a Gen2+ fw_id like
    '20231219-133953/1.1.0-g34b5d4f', and takes a device that reports a bare
    version at its word.
    """
    if not firmware_version:
        return None
    _, _, after_build_date = firmware_version.partition("/")
    return (after_build_date or firmware_version).split("-g", 1)[0]


def _version_key(version: str) -> tuple[int, ...] | None:
    """Comparable form of a version, or ``None`` when it cannot be read."""
    key = []
    for component in version.split("."):
        leading_digits = re.match(r"\d+", component)
        if leading_digits is None:
            return None
        key.append(int(leading_digits.group()))
    return tuple(key)


def _blocking_step(installed: str | None, candidate: str) -> str | None:
    """The version the device must run before ``candidate``, or ``None``."""
    if installed is None:
        return None
    installed_key = _version_key(installed)
    candidate_key = _version_key(candidate)
    if installed_key is None or candidate_key is None:
        return None
    for step, gated_from in _MANDATORY_STEPS:
        if installed_key < step and candidate_key >= gated_from:
            return ".".join(str(part) for part in step)
    return None


def _downgrade_note(installed: str | None, candidate: str) -> str | None:
    """How this update moves backwards, or ``None`` when it does not.

    Installing an older build is allowed: pinning a device to a particular
    published version is a legitimate thing to want, and an internet update
    cannot express it at all. The note exists so nobody does it unaware, since
    a device installs whatever URL it is handed without judging the version
    itself. Versions that cannot be compared carry no note.
    """
    if installed is None:
        return None
    installed_key = _version_key(installed)
    candidate_key = _version_key(candidate)
    if installed_key is None or candidate_key is None:
        return None
    if installed_key > candidate_key:
        return f"downgrade from {installed} to {candidate}"
    return None
