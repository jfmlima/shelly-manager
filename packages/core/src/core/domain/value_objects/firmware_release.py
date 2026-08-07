"""Firmware release value objects."""

from pydantic import BaseModel, ConfigDict, Field


class FirmwareRelease(BaseModel):
    """A downloadable firmware build published in the Shelly update index."""

    model_config = ConfigDict(frozen=True)

    app_name: str = Field(..., description="Device app name, e.g. 'Plus2PM'")
    version: str = Field(..., description="Firmware version, e.g. '1.7.5'")
    build_id: str = Field(..., description="Full build identifier")
    download_url: str = Field(..., description="Direct download URL for the bundle")
    channel: str = Field(default="stable", description="Release channel (stable/beta)")

    def is_installed_on(self, firmware_version: str | None) -> bool:
        """Whether a device reporting this fw_id already runs exactly this build.

        A fw_id and the index's build id name one exact build, so they decide
        this whenever the device reports one. Comparing versions instead would
        call a device current when the same version has been republished under
        a new build, which is how a reissued fix would never install. A device
        that reports a bare version has no build to compare, so its version has
        to settle it, otherwise it would be reflashed on every run.
        """
        if not firmware_version:
            return False
        if "/" in firmware_version:
            return firmware_version == self.build_id
        return firmware_version.split("-g", 1)[0] == self.version
