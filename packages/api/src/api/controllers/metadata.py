"""
Metadata API routes describing what the API itself accepts.
"""

from core.domain.entities.config_snapshot import (
    CONFIGURABLE_COMPONENT_TYPES,
    EXPORTABLE_COMPONENT_TYPES,
    NETWORK_TYPES,
)
from litestar import Router, get


@get("/component-types", tags=["Metadata"], summary="List Component Type Vocabulary")
async def list_component_types() -> dict[str, list[str]]:
    """
    List the component types the configuration endpoints accept.

    The same sets the bulk export and bulk apply request validators enforce,
    so a client can offer exactly what will be accepted instead of keeping its
    own copy that drifts as component types are added.

    Returns:
        dict: Sorted type lists, keyed exportable, configurable and network
    """
    return {
        "exportable": sorted(EXPORTABLE_COMPONENT_TYPES),
        "configurable": sorted(CONFIGURABLE_COMPONENT_TYPES),
        "network": sorted(NETWORK_TYPES),
    }


metadata_router = Router(
    path="/metadata",
    route_handlers=[list_component_types],
)
