"""Network gateway implementations."""

from .async_shelly_rpc_client import AsyncShellyRPCClient
from .legacy_http_client import LegacyHttpClient
from .mdns import MDNSGateway
from .network import NetworkGateway
from .shelly_rpc_client import ShellyRPCClient
from .zeroconf_mdns_client import ZeroconfMDNSClient

__all__ = [
    "NetworkGateway",
    "AsyncShellyRPCClient",
    "ShellyRPCClient",
    "LegacyHttpClient",
    "MDNSGateway",
    "ZeroconfMDNSClient",
]
