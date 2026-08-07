"""Abstract gateway for firmware index queries and bundle downloads."""

from abc import ABC, abstractmethod

from core.domain.value_objects.firmware_release import FirmwareRelease


class FirmwareGateway(ABC):
    @abstractmethod
    async def get_latest(
        self, app_name: str, channel: str = "stable"
    ) -> FirmwareRelease | None:
        """Latest release for an app on a channel, or ``None`` when the index has none."""
        pass

    @abstractmethod
    async def download(
        self, release: FirmwareRelease, dest_path: str
    ) -> tuple[int, str]:
        """Download a release to ``dest_path``. Returns (size_bytes, sha256)."""
        pass
