"""
Firmware store API routes for local device updates.
"""

import os
from typing import TypeVar

from core.use_cases.manage_firmware import ManageFirmware
from litestar import Router, delete, get
from litestar.exceptions import HTTPException, NotFoundException
from litestar.response import File

T = TypeVar("T")


@get("/", tags=["Firmware"], summary="List Cached Firmware Bundles")
async def list_firmware(
    manage_firmware_use_case: ManageFirmware | None = None,
) -> list[dict]:
    """
    List firmware bundles cached in the local store.

    Each bundle was downloaded once from Shelly's CDN and can be served to any
    number of devices of the same app over LAN.

    Returns:
        list[dict]: Cached bundle metadata, newest first
    """
    manage_firmware_use_case = _require(
        "manage_firmware_use_case", manage_firmware_use_case
    )

    bundles = await manage_firmware_use_case.list_bundles()
    return [
        {
            "id": bundle.id,
            "app_name": bundle.app_name,
            "version": bundle.version,
            "build_id": bundle.build_id,
            "file_name": bundle.file_name,
            "size_bytes": bundle.size_bytes,
            "sha256": bundle.sha256,
            "downloaded_at": bundle.downloaded_at,
        }
        for bundle in bundles
    ]


@delete("/{bundle_id:int}", tags=["Firmware"], summary="Delete Cached Firmware Bundle")
async def delete_firmware(
    bundle_id: int,
    manage_firmware_use_case: ManageFirmware | None = None,
) -> None:
    """
    Delete a cached firmware bundle, removing its metadata and its zip on disk.

    Args:
        bundle_id: ID of the cached bundle
    """
    manage_firmware_use_case = _require(
        "manage_firmware_use_case", manage_firmware_use_case
    )

    if not await manage_firmware_use_case.delete_bundle(bundle_id):
        raise NotFoundException(detail=f"Firmware bundle not found: {bundle_id}")


@get(
    "/{bundle_id:int}/download",
    tags=["Firmware"],
    summary="Download Cached Firmware Bundle",
)
async def download_firmware(
    bundle_id: int,
    manage_firmware_use_case: ManageFirmware | None = None,
) -> File:
    """
    Serve a cached firmware zip.

    Devices fetch this URL over LAN when an update is triggered with the local
    source; it must stay reachable from the device network without auth.

    Args:
        bundle_id: ID of the cached bundle

    Returns:
        File: The firmware zip
    """
    manage_firmware_use_case = _require(
        "manage_firmware_use_case", manage_firmware_use_case
    )

    bundle = await manage_firmware_use_case.get_bundle(bundle_id)
    if bundle is None:
        raise NotFoundException(detail=f"Firmware bundle not found: {bundle_id}")

    path = manage_firmware_use_case.bundle_path(bundle)
    if not os.path.isfile(path):
        raise NotFoundException(
            detail=f"Firmware bundle {bundle_id} has no file on disk"
        )

    return File(
        path=path,
        filename=bundle.file_name,
        media_type="application/zip",
    )


firmware_router = Router(
    path="/firmware",
    route_handlers=[
        list_firmware,
        delete_firmware,
        download_firmware,
    ],
)


def _require(dep_name: str, dep: T | None) -> T:
    if dep is None:
        raise HTTPException(status_code=500, detail=f"Missing dependency: {dep_name}")
    return dep
