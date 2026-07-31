"""
Device gateway implementation for Shelly devices.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from ...domain.entities.device_status import DeviceStatus
from ...domain.entities.discovered_device import DiscoveredDevice
from ...domain.entities.exceptions import (
    ConfigurationError,
    DeviceAuthenticationError,
    DeviceCommunicationError,
    DeviceUnreachableError,
)
from ...domain.enums.enums import Status
from ...domain.value_objects.action_envelope import ActionEnvelope
from ...domain.value_objects.action_name import ActionName
from ...domain.value_objects.action_result import ActionResult
from ...services.auth_state_cache import AuthStateCache
from ...utils.validation import normalize_mac
from ..network.network import RpcNetworkGateway
from ..network.rpc_envelope import RpcError, rpc_result
from .device import DeviceGateway
from .legacy_device_gateway import LegacyDeviceGateway
from .legacy_route import LegacyRoute
from .rpc_methods import RpcMethods
from .rpc_read import RpcRead

logger = logging.getLogger(__name__)

SHELLY_SYSTEM_ACTIONS = {"Update", "Reboot", "FactoryReset"}


class ShellyDeviceGateway(DeviceGateway):

    def __init__(
        self,
        rpc_client: RpcNetworkGateway,
        timeout: float = 10.0,
        legacy_gateway: LegacyDeviceGateway | None = None,
        auth_state_cache: AuthStateCache | None = None,
    ) -> None:
        self._rpc_client = rpc_client
        self.timeout = timeout
        self._legacy = LegacyRoute(legacy_gateway)
        self._auth_state_cache = auth_state_cache
        self._method_lists: dict[str, list[str]] = {}

    def invalidate_legacy_credential_cache(self, mac: str) -> None:
        self._legacy.invalidate_credentials(mac)

    async def get_legacy_settings(self, ip: str) -> dict[str, Any] | None:
        return await self._legacy.get_settings(ip)

    async def discover_device(
        self, ip: str, timeout: float | None = None
    ) -> DiscoveredDevice | None:
        """
        Discover basic device information (original get_device_status logic).

        Args:
            ip: Device IP address
            timeout: Per-request timeout in seconds; falls back to the gateway
                default when not provided.

        Returns:
            DiscoveredDevice with basic info and update status, or None if unreachable
        """
        effective_timeout = timeout if timeout is not None else self.timeout
        try:
            device_info, response_time = await self._rpc_client.make_rpc_request(
                ip, RpcMethods.GET_DEVICE_INFO, timeout=effective_timeout
            )
            device_data = device_info.get("result", device_info)

            auth_required = device_data.get("auth_en", False)

            if self._auth_state_cache is not None:
                if auth_required:
                    self._auth_state_cache.mark_auth_required(normalize_mac(ip))
                else:
                    device_id = device_data.get("id") or ip
                    auth_required = self._auth_state_cache.requires_auth(device_id)

            device = DiscoveredDevice(
                ip=ip,
                status=Status.DETECTED,
                device_id=device_data.get("id"),
                device_type=device_data.get("model"),
                device_name=device_data.get("name"),
                firmware_version=device_data.get("fw_id"),
                auth_required=auth_required,
                response_time=response_time,
                last_seen=datetime.now(),
            )

            try:
                update_info, _ = await self._rpc_client.make_rpc_request(
                    ip, RpcMethods.CHECK_FOR_UPDATE, timeout=effective_timeout
                )
                update_data = update_info.get("result", update_info)

                stable_update = update_data.get("stable", {}) if update_data else {}
                beta_update = update_data.get("beta", {}) if update_data else {}

                if stable_update.get("version") or beta_update.get("version"):
                    device.status = Status.UPDATE_AVAILABLE
                else:
                    device.status = Status.NO_UPDATE_NEEDED

            except Exception as e:
                logger.error(f"Error checking for updates: {e}", exc_info=True)
                pass

            return device

        except DeviceUnreachableError as e:
            # No TCP connection established: nothing is listening here. A Gen1
            # device would still accept the connection, so there's no point
            # paying for a second (legacy) probe on a dead address.
            logger.debug("Host %s unreachable, skipping legacy probe: %s", ip, e)
            return DiscoveredDevice(
                ip=ip,
                status=Status.UNREACHABLE,
                error_message=str(e),
                last_seen=datetime.now(),
            )

        except ConfigurationError:
            raise

        except Exception as e:
            logger.debug(
                "RPC discovery failed for %s, attempting legacy HTTP fallback: %s",
                ip,
                e,
            )
            legacy_device = await self._legacy.discover_device(ip, effective_timeout)
            if legacy_device:
                return legacy_device

            return DiscoveredDevice(
                ip=ip,
                status=Status.UNREACHABLE,
                error_message=str(e),
                last_seen=datetime.now(),
            )

    async def get_device_status(self, ip: str) -> DeviceStatus | None:
        """
        Get device components and detailed status information.

        Args:
            ip: Device IP address

        Returns:
            DeviceStatus with all component data, or None if unreachable
        """
        try:
            status = await self._read_status_over_rpc(ip)
            if status is not None:
                return status
            logger.debug("No RPC read answered for %s, attempting legacy fallback", ip)
        except DeviceAuthenticationError:
            raise
        except Exception as e:
            logger.error(
                f"Error getting device status via RPC, attempting legacy fallback: {e}",
                exc_info=True,
            )

        return await self._legacy.get_device_status(ip)

    async def get_component_keys(self, ip: str, component_type: str) -> list[str]:
        """Get component keys for a given type using a single RPC call."""
        try:
            response, _ = await self._rpc_client.make_rpc_request(
                ip,
                RpcMethods.GET_COMPONENTS,
                params={"offset": 0},
                timeout=self.timeout,
            )
            components = response.get("result", response).get("components", [])
            return [
                c["key"]
                for c in components
                if c.get("key", "").split(":")[0] == component_type
            ]
        except Exception:
            return []

    async def _get_available_methods(self, ip: str) -> list[str]:
        """Get available RPC methods for action validation.

        Args:
            ip: Device IP address

        Returns:
            The device's RPC method names. Empty when there is no list to check
            against, whether the device could not be asked or answered with
            something unreadable; callers treat both as "unvalidated" rather
            than as proof that a method does not exist.

        A list this asks for is always read fresh from the device, and is the
        one _resolve_method hands to the next action on the same device.
        """
        methods = await self._fetch_available_methods(ip)
        if methods:
            self._method_lists[ip] = list(methods)
        return methods

    async def execute_component_action(
        self,
        ip: str,
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Execute validated action on any component type.

        Args:
            ip: Device IP address
            component_key: Component key (e.g., 'switch:0', 'sys', 'zigbee')
            action: Action name, bare or qualified (e.g., 'Toggle', 'Switch.Toggle')
            parameters: Action-specific parameters (e.g., {'channel': 'beta'})

        Returns:
            ActionResult with success/failure details
        """
        action_name = ActionName.of(action)
        envelope = ActionEnvelope(
            device_ip=ip, action_type=f"{component_key}.{action_name.method}"
        )

        try:
            if action_name.is_legacy:
                return await self._legacy.execute_action(
                    ip, component_key, action, parameters
                )

            rpc_method = await self._resolve_method(ip, component_key, action_name)

            if rpc_method is None:
                return envelope.failed(
                    message=f"Action {action} not supported by {component_key}",
                    error=f"Component {component_key} has no method {action}",
                )

            params: dict[str, Any] = {}
            if ":" in component_key and component_key != "sys":
                try:
                    params["id"] = int(component_key.split(":")[1])
                except (IndexError, ValueError):
                    return envelope.failed(
                        message=f"Invalid component key format: {component_key}",
                        error=f"Could not parse component ID from {component_key}",
                    )

            if parameters:
                params.update(parameters)

            response, _ = await self._rpc_client.make_rpc_request(
                ip, rpc_method, params=params or None, timeout=self.timeout
            )

            return envelope.succeeded(
                message=(
                    f"{action_name.method} executed successfully on {component_key}"
                ),
                data=rpc_result(response),
            )

        except RpcError as e:
            # The device answered, and refused. That is a failed action, not a
            # transport problem, and it carries the device's own reason.
            return envelope.failed(
                message=f"{action_name.method} failed on {component_key}",
                error=str(e),
            )

        except ConfigurationError:
            raise

        except Exception as e:
            err = str(e)
            if "401" in err or "unauthorized" in err.lower():
                error_message = DeviceAuthenticationError(ip, err).message
            else:
                error_message = DeviceCommunicationError(ip, err, err).message

            return envelope.failed(
                message=f"Action failed: {err}",
                error=error_message,
            )

    async def execute_bulk_action(
        self,
        device_ips: list[str],
        component_key: str,
        action: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[ActionResult]:
        """Execute component actions on multiple devices in parallel.

        Only supports specific bulk operations:
        - shelly.Update: Firmware updates
        - shelly.Reboot: Device reboot
        - shelly.FactoryReset: Factory reset

        Args:
            device_ips: List of device IP addresses
            component_key: Component key (must be 'shelly' for bulk operations)
            action: Action name (Update, Reboot, FactoryReset)

        Returns:
            List of ActionResult objects

        Raises:
            ValueError: If component_key/action combination is not supported for bulk operations
        """
        action_name = ActionName.of(action)

        namespace = action_name.namespace
        allowed = {a.lower() for a in SHELLY_SYSTEM_ACTIONS}

        if (
            component_key.lower() != "shelly"
            or (namespace is not None and namespace.lower() != "shelly")
            or action_name.method.lower() not in allowed
        ):
            raise ValueError(
                f"Bulk operation '{component_key}.{action}' is not supported. "
                f"Supported actions on the shelly component: "
                f"{', '.join(sorted(SHELLY_SYSTEM_ACTIONS))}"
            )

        tasks = [
            self.execute_component_action(ip, component_key, action, parameters)
            for ip in device_ips
        ]

        return await asyncio.gather(*tasks, return_exceptions=False)

    async def _read_status_over_rpc(self, ip: str) -> DeviceStatus | None:
        """Ask the device for its status every way at once.

        The device is already known to exist here, so these independent reads
        are issued concurrently rather than one round-trip at a time, and each
        one is optional: a device that answers only some of them still has a
        status worth reporting. None means it answered none of them, which is
        what a Gen1 device looks like from this side.
        """
        device_info_res, components_res, status_res, methods_res = await asyncio.gather(
            self._rpc_client.make_rpc_request(
                ip, RpcMethods.GET_DEVICE_INFO, timeout=self.timeout
            ),
            self._rpc_client.make_rpc_request(
                ip,
                RpcMethods.GET_COMPONENTS,
                params={"offset": 0},
                timeout=self.timeout,
            ),
            self._rpc_client.make_rpc_request(
                ip, RpcMethods.GET_STATUS, timeout=self.timeout
            ),
            self._get_available_methods(ip),
            return_exceptions=True,
        )

        # Only these two: a device info read that fails still leaves a status
        # worth building, so it is logged rather than raised.
        for res in (components_res, status_res):
            if isinstance(res, DeviceAuthenticationError):
                raise res

        device_info = RpcRead.of(device_info_res, "device info")
        self._remember_auth_requirement(ip, device_info.body)

        components = RpcRead.of(components_res, "components", missing={})
        status = RpcRead.of(status_res, "device status")

        # The method list cannot join them: it comes back empty both when the
        # device has none to report and when the read failed.
        if not (device_info.answered or components.answered or status.answered):
            return None

        return DeviceStatus.from_raw_response(
            ip,
            components.body,
            available_methods=(
                [] if isinstance(methods_res, BaseException) else methods_res
            ),
            device_info_data=device_info.body,
            status_data=status.body,
        )

    def _remember_auth_requirement(self, ip: str, device_info: Any) -> None:
        """Record that a device asks for credentials, so later calls send them."""
        if not device_info or not device_info.get("auth_en", False):
            return
        if self._auth_state_cache is not None:
            self._auth_state_cache.mark_auth_required(normalize_mac(ip))

    async def _fetch_available_methods(self, ip: str) -> list[str]:
        try:
            methods_response, _ = await self._rpc_client.make_rpc_request(
                ip, RpcMethods.LIST_METHODS, timeout=self.timeout
            )
            result = methods_response.get("result", methods_response)
            if isinstance(result, dict) and isinstance(result.get("methods"), list):
                return [m for m in result["methods"] if isinstance(m, str)]

            logger.warning("Unreadable method list from %s: %r", ip, result)
            return []
        except Exception as e:
            logger.warning(f"Failed to get available methods for {ip}: {e}")
            return []

    async def _resolve_method(
        self, ip: str, component_key: str, action_name: ActionName
    ) -> str | None:
        """The method to send, spending a round trip only when one would help.

        Reading a device's status fetches its method list, so an action taken
        from a status page already has the answer and need not ask again.

        A remembered list that refuses is asked again before the refusal
        stands, which is the round trip the device would have been asked for
        anyway, so an action the device has gained since is never wrongly
        refused. A remembered list that accepts is taken at its word: a method
        the device has since dropped is sent and rejected by the device rather
        than refused here, and the next status read corrects the list.
        """
        remembered = self._method_lists.get(ip)
        if remembered is None:
            return action_name.resolve(
                component_key, await self._get_available_methods(ip)
            )

        rpc_method = action_name.resolve(component_key, remembered)
        if rpc_method is not None:
            return rpc_method

        return action_name.resolve(component_key, await self._get_available_methods(ip))
