"""Use case for provisioning a new Shelly device via its AP."""

import asyncio
import hashlib
import logging
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from typing import Any

from core.domain.entities.exceptions import (
    DeviceCommunicationError,
    DeviceNotFoundError,
)
from core.domain.entities.provisioning_profile import ProvisioningProfile
from core.domain.value_objects.provision_request import (
    APDeviceInfo,
    DetectDeviceRequest,
    ProvisionDeviceRequest,
    ProvisionResult,
    ProvisionStep,
)
from core.gateways.device.ap_device_detector import APDeviceDetector
from core.gateways.device.rpc_methods import RpcMethods
from core.gateways.network.network import RpcNetworkGateway
from core.repositories.credentials_repository import CredentialsRepository
from core.repositories.provisioning_profile_repository import (
    ProvisioningProfileRepository,
)
from core.utils.target_parser import expand_targets

logger = logging.getLogger(__name__)


class ProvisionDeviceUseCase:
    """Orchestrates the full provisioning flow for a new Shelly device."""

    def __init__(
        self,
        rpc_client: RpcNetworkGateway,
        detector: APDeviceDetector,
        profile_repository_factory: Callable[
            [], AbstractAsyncContextManager[ProvisioningProfileRepository]
        ],
        credentials_repository_factory: Callable[
            [], AbstractAsyncContextManager[CredentialsRepository]
        ],
    ):
        self._rpc_client = rpc_client
        self._detector = detector
        self._profile_repo_factory = profile_repository_factory
        self._credentials_repo_factory = credentials_repository_factory

    async def detect(self, request: DetectDeviceRequest) -> APDeviceInfo:
        """Detect a device at the given AP IP.

        This is a standalone operation for the 'detect' endpoint/command.
        """
        return await self._detector.detect(request.device_ip, request.timeout)

    async def execute(self, request: ProvisionDeviceRequest) -> ProvisionResult:
        """Execute the full provisioning flow.

        Steps:
            1. Detect device at AP IP
            2. Resolve provisioning profile
            3. Set device name & timezone (Sys.SetConfig) - non-critical
            4. Set authentication (Shelly.SetAuth) - non-critical
            5. Configure MQTT (MQTT.SetConfig) - non-critical
            6. Disable cloud (Cloud.SetConfig) - non-critical
            7. Configure Wi-Fi station (WiFi.SetConfig) - CRITICAL, last step
            8. Reboot if needed

        Non-critical steps log failures and continue.
        Wi-Fi failure aborts the entire flow.
        """
        steps_completed: list[ProvisionStep] = []
        steps_failed: list[ProvisionStep] = []
        needs_reboot = False
        auth_credentials: tuple[str, str] | None = None

        # Step 1: Detect device
        try:
            device_info = await self._detector.detect(
                request.device_ip, request.timeout
            )
        except (DeviceNotFoundError, DeviceCommunicationError) as e:
            step = ProvisionStep(name="detect", success=False, message=str(e))
            return ProvisionResult(
                success=False,
                steps_completed=[],
                steps_failed=[step],
                error=f"Device detection failed: {e}",
            )

        steps_completed.append(
            ProvisionStep(
                name="detect",
                success=True,
                message=f"Detected {device_info.app or device_info.model} "
                f"(gen{device_info.generation}, MAC: {device_info.mac})",
            )
        )

        # Step 2: Resolve profile
        profile = await self._resolve_profile(request.profile_id)
        if profile is None:
            step = ProvisionStep(
                name="resolve_profile",
                success=False,
                message="No provisioning profile found. Create a profile first.",
            )
            return ProvisionResult(
                success=False,
                device_id=device_info.device_id,
                device_model=device_info.model,
                device_mac=device_info.mac,
                generation=device_info.generation,
                steps_completed=steps_completed,
                steps_failed=[step],
                error="No provisioning profile available",
            )

        steps_completed.append(
            ProvisionStep(
                name="resolve_profile",
                success=True,
                message=f"Using profile: {profile.name}",
            )
        )

        device_template_vars = {
            "device_id": device_info.device_id,
            "model": device_info.model,
            "app": device_info.app or "",
            "mac": device_info.mac,
        }

        # Step 3: Set device name & timezone (non-critical)
        if profile.device_name_template or profile.timezone:
            step, restart = await self._configure_sys(
                request.device_ip,
                device_info,
                profile,
                device_template_vars,
                request.timeout,
                auth_credentials,
            )
            if step.success:
                steps_completed.append(step)
                needs_reboot = needs_reboot or restart
            else:
                steps_failed.append(step)
                logger.warning("Sys config failed (non-critical): %s", step.message)

        # Step 4: Set authentication (non-critical)
        if profile.auth_password:
            step, new_auth = await self._configure_auth(
                request.device_ip,
                device_info,
                profile,
                request.timeout,
                auth_credentials,
            )
            if step.success:
                steps_completed.append(step)
                auth_credentials = new_auth
            else:
                steps_failed.append(step)
                logger.warning("Auth config failed (non-critical): %s", step.message)

        # Step 5: Configure MQTT (non-critical)
        if profile.mqtt_enabled and profile.mqtt_server:
            step, restart = await self._configure_mqtt(
                request.device_ip,
                device_info,
                profile,
                device_template_vars,
                request.timeout,
                auth_credentials,
            )
            if step.success:
                steps_completed.append(step)
                needs_reboot = needs_reboot or restart
            else:
                steps_failed.append(step)
                logger.warning("MQTT config failed (non-critical): %s", step.message)

        # Step 6: Disable cloud (non-critical)
        if not profile.cloud_enabled:
            step, restart = await self._configure_cloud(
                request.device_ip,
                request.timeout,
                auth_credentials,
            )
            if step.success:
                steps_completed.append(step)
                needs_reboot = needs_reboot or restart
            else:
                steps_failed.append(step)
                logger.warning("Cloud config failed (non-critical): %s", step.message)

        # Step 7: Configure Wi-Fi station - CRITICAL, last before reboot
        if profile.wifi_ssid:
            step, restart = await self._configure_wifi(
                request.device_ip,
                profile,
                request.timeout,
                auth_credentials,
            )
            if step.success:
                steps_completed.append(step)
                needs_reboot = needs_reboot or restart
            else:
                steps_failed.append(step)
                return ProvisionResult(
                    success=False,
                    device_id=device_info.device_id,
                    device_model=device_info.model,
                    device_mac=device_info.mac,
                    generation=device_info.generation,
                    steps_completed=steps_completed,
                    steps_failed=steps_failed,
                    error=f"Wi-Fi configuration failed: {step.message}",
                )

        # Step 8: Reboot if needed
        if needs_reboot:
            step = await self._reboot(
                request.device_ip, request.timeout, auth_credentials
            )
            # Reboot may fail if connection already dropped after WiFi config
            # That's OK - the device will reboot anyway
            steps_completed.append(step)

        return ProvisionResult(
            success=True,
            device_id=device_info.device_id,
            device_model=device_info.model,
            device_mac=device_info.mac,
            generation=device_info.generation,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            needs_verification=profile.wifi_ssid is not None,
        )

    async def verify(
        self,
        device_mac: str,
        scan_targets: list[str],
        timeout: float = 30.0,
    ) -> str | None:
        """Verify a device is reachable on the target network by MAC.

        Args:
            device_mac: MAC address to look for.
            scan_targets: Network targets to scan (e.g., ["192.168.1.0/24"]).
            timeout: Scan timeout.

        Returns:
            The device's new IP if found, None otherwise.
        """
        normalized_mac = device_mac.upper().replace(":", "")
        ips = expand_targets(scan_targets)
        semaphore = asyncio.Semaphore(50)

        async def probe_ip(ip: str) -> str | None:
            async with semaphore:
                try:
                    info = await self._detector.detect(ip, timeout=3.0)
                    if info.mac.upper().replace(":", "") == normalized_mac:
                        return ip
                except Exception:
                    pass
                return None

        tasks = [probe_ip(ip) for ip in ips]
        results = await asyncio.gather(*tasks)

        for result in results:
            if result is not None:
                return result

        return None

    async def _resolve_profile(
        self, profile_id: int | None
    ) -> ProvisioningProfile | None:
        """Resolve the profile to use for provisioning."""
        async with self._profile_repo_factory() as repository:
            if profile_id is not None:
                return await repository.get(profile_id)
            return await repository.get_default()

    async def _make_rpc_call(
        self,
        ip: str,
        method: str,
        params: dict[str, Any] | None,
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> dict[str, Any]:
        """Make an RPC call, returning the result dict."""
        response, _ = await self._rpc_client.make_rpc_request(
            ip=ip,
            method=method,
            params=params,
            auth=auth,
            timeout=timeout,
        )
        # RPC response has either 'result' or 'error'
        if "error" in response:
            error = response["error"]
            raise DeviceCommunicationError(
                ip,
                f"{error.get('message', 'Unknown error')} (code: {error.get('code')})",
            )
        result: dict[str, Any] = response.get("result", {})
        return result

    async def _configure_sys(
        self,
        ip: str,
        device_info: APDeviceInfo,
        profile: ProvisioningProfile,
        template_vars: dict[str, str],
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> tuple[ProvisionStep, bool]:
        """Configure system settings (device name, timezone)."""
        config: dict[str, Any] = {}

        if profile.device_name_template:
            device_name = profile.expand_template(
                profile.device_name_template, template_vars
            )
            config["device"] = {"name": device_name}

        if profile.timezone:
            if "device" not in config:
                config["device"] = {}
            config.setdefault("location", {})["tz"] = profile.timezone

        try:
            result = await self._make_rpc_call(
                ip,
                RpcMethods.SYS_SET_CONFIG,
                {"config": config},
                timeout,
                auth,
            )
            restart = result.get("restart_required", False)
            return (
                ProvisionStep(
                    name="set_sys",
                    success=True,
                    message="System config applied (name/timezone)",
                    restart_required=restart,
                ),
                restart,
            )
        except Exception as e:
            return (
                ProvisionStep(name="set_sys", success=False, message=str(e)),
                False,
            )

    async def _configure_auth(
        self,
        ip: str,
        device_info: APDeviceInfo,
        profile: ProvisioningProfile,
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> tuple[ProvisionStep, tuple[str, str] | None]:
        """Configure device authentication via Shelly.SetAuth."""
        if not profile.auth_password:
            return (
                ProvisionStep(
                    name="set_auth", success=True, message="No auth password configured"
                ),
                auth,
            )

        try:
            # Compute HA1: SHA256("admin:<device_id>:<password>")
            realm = device_info.auth_domain or device_info.device_id
            ha1_input = f"admin:{realm}:{profile.auth_password}"
            ha1 = hashlib.sha256(ha1_input.encode()).hexdigest()

            await self._make_rpc_call(
                ip,
                RpcMethods.SET_AUTH,
                {"user": "admin", "realm": realm, "ha1": ha1},
                timeout,
                auth,
            )

            new_auth = ("admin", profile.auth_password)

            # Store credentials in the database
            await self._store_credentials(
                device_info.mac, "admin", profile.auth_password, ip
            )

            return (
                ProvisionStep(
                    name="set_auth",
                    success=True,
                    message="Authentication configured and credentials stored",
                ),
                new_auth,
            )
        except Exception as e:
            return (
                ProvisionStep(name="set_auth", success=False, message=str(e)),
                auth,
            )

    async def _store_credentials(
        self, mac: str, username: str, password: str, ip: str
    ) -> None:
        """Store device credentials in the credentials repository."""
        try:
            async with self._credentials_repo_factory() as repo:
                await repo.set(
                    mac=mac,
                    username=username,
                    password=password,
                    last_seen_ip=ip,
                )
            logger.info("Stored credentials for device MAC: %s", mac)
        except Exception as e:
            logger.error("Failed to store credentials for %s: %s", mac, e)

    async def _configure_mqtt(
        self,
        ip: str,
        device_info: APDeviceInfo,
        profile: ProvisioningProfile,
        template_vars: dict[str, str],
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> tuple[ProvisionStep, bool]:
        """Configure MQTT settings."""
        config: dict[str, Any] = {
            "enable": True,
            "server": profile.mqtt_server,
        }

        if profile.mqtt_user:
            config["user"] = profile.mqtt_user
        if profile.mqtt_password:
            config["pass"] = profile.mqtt_password

        if profile.mqtt_topic_prefix_template:
            topic_prefix = profile.expand_template(
                profile.mqtt_topic_prefix_template, template_vars
            )
            config["topic_prefix"] = topic_prefix

        try:
            result = await self._make_rpc_call(
                ip,
                RpcMethods.MQTT_SET_CONFIG,
                {"config": config},
                timeout,
                auth,
            )
            restart = result.get("restart_required", True)
            return (
                ProvisionStep(
                    name="set_mqtt",
                    success=True,
                    message=f"MQTT configured (server: {profile.mqtt_server})",
                    restart_required=restart,
                ),
                restart,
            )
        except Exception as e:
            return (
                ProvisionStep(name="set_mqtt", success=False, message=str(e)),
                False,
            )

    async def _configure_cloud(
        self,
        ip: str,
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> tuple[ProvisionStep, bool]:
        """Disable cloud connectivity."""
        try:
            result = await self._make_rpc_call(
                ip,
                RpcMethods.CLOUD_SET_CONFIG,
                {"config": {"enable": False}},
                timeout,
                auth,
            )
            restart = result.get("restart_required", False)
            return (
                ProvisionStep(
                    name="set_cloud",
                    success=True,
                    message="Cloud disabled",
                    restart_required=restart,
                ),
                restart,
            )
        except Exception as e:
            return (
                ProvisionStep(name="set_cloud", success=False, message=str(e)),
                False,
            )

    async def _configure_wifi(
        self,
        ip: str,
        profile: ProvisioningProfile,
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> tuple[ProvisionStep, bool]:
        """Configure Wi-Fi station. This is the last step before reboot.

        After this call, the device will reconnect to the target network
        and the AP connection will drop ~1s later.
        """
        if not profile.wifi_ssid:
            return (
                ProvisionStep(
                    name="set_wifi",
                    success=True,
                    message="No Wi-Fi SSID configured",
                ),
                False,
            )

        config: dict[str, Any] = {
            "sta": {
                "ssid": profile.wifi_ssid,
                "enable": True,
            }
        }

        if profile.wifi_password:
            config["sta"]["pass"] = profile.wifi_password
            config["sta"]["is_open"] = False
        else:
            config["sta"]["is_open"] = True

        try:
            result = await self._make_rpc_call(
                ip,
                RpcMethods.WIFI_SET_CONFIG,
                {"config": config},
                timeout,
                auth,
            )
            restart = result.get("restart_required", False)
            return (
                ProvisionStep(
                    name="set_wifi",
                    success=True,
                    message=f"Wi-Fi configured (SSID: {profile.wifi_ssid})",
                    restart_required=restart,
                ),
                restart,
            )
        except DeviceCommunicationError:
            # Connection may drop immediately after WiFi config
            # This is expected behavior - treat as success
            return (
                ProvisionStep(
                    name="set_wifi",
                    success=True,
                    message=f"Wi-Fi configured (SSID: {profile.wifi_ssid}) "
                    "- connection dropped as expected",
                    restart_required=True,
                ),
                True,
            )
        except Exception as e:
            return (
                ProvisionStep(name="set_wifi", success=False, message=str(e)),
                False,
            )

    async def _reboot(
        self,
        ip: str,
        timeout: float,
        auth: tuple[str, str] | None,
    ) -> ProvisionStep:
        """Reboot the device."""
        try:
            await self._make_rpc_call(
                ip,
                RpcMethods.REBOOT,
                {"delay_ms": 1000},
                timeout,
                auth,
            )
            return ProvisionStep(
                name="reboot",
                success=True,
                message="Reboot command sent",
            )
        except Exception:
            # Reboot may fail if connection dropped (after WiFi config)
            # The device will reboot anyway from the WiFi reconnect
            return ProvisionStep(
                name="reboot",
                success=True,
                message="Reboot command sent (connection may have dropped)",
            )
