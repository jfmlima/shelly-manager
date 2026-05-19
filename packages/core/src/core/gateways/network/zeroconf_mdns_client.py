import asyncio
import logging
import socket
from typing import Any

from zeroconf import ServiceListener, Zeroconf
from zeroconf.asyncio import AsyncServiceBrowser, AsyncZeroconf

from .mdns import MDNSGateway

logger = logging.getLogger(__name__)


class ZeroconfMDNSClient(MDNSGateway):

    def __init__(self) -> None:
        self._discovered_ips: set[str] = set()

    async def discover_device_ips(
        self, timeout: float = 10.0, service_types: list[str] | None = None
    ) -> list[str]:
        if service_types is None:
            service_types = ["_http._tcp.local.", "_shelly._tcp.local."]

        self._discovered_ips.clear()

        # Fresh AsyncZeroconf per scan - avoids zombie browser threads
        # from accumulating across multiple scan calls
        aiozc = AsyncZeroconf()
        try:
            browsers = []

            for service_type in service_types:
                listener = ShellyServiceListener(self._discovered_ips)
                browser = AsyncServiceBrowser(
                    aiozc.zeroconf, service_type, listener=listener
                )
                browsers.append(browser)

            logger.info(f"Starting mDNS discovery for {timeout} seconds...")
            await asyncio.sleep(timeout)

            for browser in browsers:
                await browser.async_cancel()

            discovered_list = list(self._discovered_ips)
            logger.info(
                f"mDNS discovery completed. Found {len(discovered_list)} devices: {discovered_list}"
            )

            return discovered_list

        except Exception as e:
            logger.error(f"Error during mDNS discovery: {e}", exc_info=True)
            return []

        finally:
            # Always clean up, even on exception
            try:
                await aiozc.async_close()
            except Exception as e:
                logger.error(f"Error cleaning up AsyncZeroconf: {e}", exc_info=True)

    async def close(self) -> None:
        # Nothing to close - each scan cleans up after itself
        pass


class ShellyServiceListener(ServiceListener):
    def __init__(self, discovered_ips: set[str]):
        self.discovered_ips = discovered_ips

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        # Schedule the blocking get_service_info call off the event loop
        asyncio.get_event_loop().run_in_executor(
            None, self._resolve_service, zc, type_, name
        )

    def _resolve_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        try:
            logger.debug(f"Discovered service: {name} of type {type_}")

            info = zc.get_service_info(type_, name)
            if info is None:
                logger.debug(f"No service info available for {name}")
                return

            for address in info.addresses:
                try:
                    ip = socket.inet_ntoa(address)

                    if self._is_likely_shelly_device(name, info):
                        self.discovered_ips.add(ip)
                        logger.info(f"Added Shelly device IP: {ip} (service: {name})")
                    else:
                        logger.debug(
                            f"Skipping non-Shelly device: {ip} (service: {name})"
                        )

                except (OSError, ValueError) as e:
                    logger.debug(f"Error converting address to IP: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error processing service {name}: {e}", exc_info=True)

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logger.debug(f"Service removed: {name} of type {type_}")

    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        logger.debug(f"Service updated: {name} of type {type_}")

    def _is_likely_shelly_device(self, name: str, info: Any) -> bool:
        name_lower = name.lower()
        if any(
            pattern in name_lower for pattern in ["shelly", "shellyplus", "shellypro"]
        ):
            return True

        if hasattr(info, "properties") and info.properties:
            try:
                props_str = str(info.properties).lower()
                if any(pattern in props_str for pattern in ["shelly", "allterco"]):
                    return True
            except Exception as e:
                logger.debug(f"Error checking TXT records: {e}")

        if "_http._tcp" in name_lower:
            return True

        return False