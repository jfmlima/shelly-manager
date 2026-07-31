"""Cached firmware bundle domain entity."""

from dataclasses import dataclass


@dataclass
class FirmwareBundle:
    """A firmware zip cached on the manager host and served to devices over LAN.

    The zip blob lives on disk under the configured firmware directory as
    ``file_name``; only metadata is persisted in the database.
    """

    app_name: str
    version: str
    build_id: str
    file_name: str
    size_bytes: int = 0
    sha256: str | None = None
    id: int | None = None
    downloaded_at: int | None = None
