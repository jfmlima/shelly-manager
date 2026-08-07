"""Firmware gateway backed by the official Shelly update index and CDN."""

import hashlib
import logging
import os
import re
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from core.domain.entities.exceptions import FirmwareError
from core.domain.value_objects.firmware_release import FirmwareRelease

from .firmware import FirmwareGateway

logger = logging.getLogger(__name__)

_SAFE_APP_NAME = re.compile(r"[A-Za-z0-9._-]+")
_MAX_BUNDLE_SIZE_BYTES = 100 * 1024 * 1024
_MAX_DOWNLOAD_REDIRECTS = 5


class ShellyCloudFirmwareGateway(FirmwareGateway):
    """Fetches firmware metadata and bundles from Shelly's public endpoints.

    The index endpoint is undocumented (the same dependency the community
    tools take), so a missing or unexpected response means "no release",
    never a crash.
    """

    def __init__(
        self,
        index_url: str,
        session: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
        connect_timeout: float = 5.0,
        verify: bool = True,
        allowed_download_hosts: list[str] | None = None,
    ) -> None:
        self._index_url = index_url.rstrip("/")
        self._allowed_download_hosts = tuple(
            normalised
            for host in (
                ["shelly.cloud"]
                if allowed_download_hosts is None
                else allowed_download_hosts
            )
            if (normalised := _normalise_host(host))
        )
        if session is not None:
            self._session = session
        else:
            self._session = httpx.AsyncClient(
                timeout=httpx.Timeout(timeout, connect=connect_timeout),
                follow_redirects=True,
                verify=verify,
            )

    async def get_latest(
        self, app_name: str, channel: str = "stable"
    ) -> FirmwareRelease | None:
        if not _is_safe_app_name(app_name):
            raise FirmwareError(
                f"Refusing firmware lookup for unsafe app name '{app_name}'",
                {"app_name": app_name},
            )

        url = f"{self._index_url}/{app_name}"
        logger.info("Querying Shelly firmware index: %s", url)
        try:
            response = await self._session.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError) as e:
            raise FirmwareError(
                f"Firmware index request failed for {app_name}: {e}",
                {"app_name": app_name},
            ) from e

        return _release_from_index_entry(app_name, data, channel)

    async def download(
        self, release: FirmwareRelease, dest_path: str
    ) -> tuple[int, str]:
        logger.info("Downloading firmware bundle: %s", release.download_url)
        tmp_path = f"{dest_path}.{uuid.uuid4().hex}.part"
        digest = hashlib.sha256()
        size = 0
        url = release.download_url
        try:
            for _ in range(_MAX_DOWNLOAD_REDIRECTS + 1):
                self._reject_untrusted_download(url, release)
                async with self._session.stream(
                    "GET",
                    url,
                    headers={"Accept-Encoding": "identity"},
                    follow_redirects=False,
                ) as response:
                    if response.is_redirect:
                        url = _redirect_target(response, release)
                        continue

                    response.raise_for_status()
                    _reject_compressed(response, release)
                    _reject_oversized(response, release)
                    with open(tmp_path, "wb") as handle:
                        # Only safe because an encoded body was refused above:
                        # httpx decodes a whole chunk before yielding it.
                        async for chunk in response.aiter_bytes():
                            size += len(chunk)
                            if size > _MAX_BUNDLE_SIZE_BYTES:
                                raise FirmwareError(
                                    f"Firmware download for {release.app_name}"
                                    f" {release.version} exceeded"
                                    f" {_MAX_BUNDLE_SIZE_BYTES} bytes",
                                    {
                                        "app_name": release.app_name,
                                        "version": release.version,
                                    },
                                )
                            handle.write(chunk)
                            digest.update(chunk)
                    if size == 0:
                        raise FirmwareError(
                            f"Firmware download for {release.app_name}"
                            f" {release.version} was empty",
                            {
                                "app_name": release.app_name,
                                "version": release.version,
                            },
                        )
                    break
            else:
                raise FirmwareError(
                    f"Firmware download for {release.app_name} {release.version}"
                    f" redirected more than {_MAX_DOWNLOAD_REDIRECTS} times",
                    {"app_name": release.app_name, "version": release.version},
                )
            os.replace(tmp_path, dest_path)
        except (httpx.HTTPError, httpx.InvalidURL, OSError, UnicodeError) as e:
            raise FirmwareError(
                f"Firmware download failed for {release.app_name}"
                f" {release.version}: {e}",
                {"app_name": release.app_name, "version": release.version},
            ) from e
        finally:
            Path(tmp_path).unlink(missing_ok=True)
        return size, digest.hexdigest()

    async def close(self) -> None:
        await self._session.aclose()

    def _reject_untrusted_download(self, url: str, release: FirmwareRelease) -> None:
        """Refuse a download address firmware should never come from.

        The index response decides where a bundle lives, and TLS verification
        is off by default because Shelly signs those endpoints privately. A
        substituted response, or a redirect from a host that honours one,
        could otherwise make the manager fetch any address it can reach and
        hand the body back through the unauthenticated download route.
        """
        parsed = urlparse(url)
        details = {"app_name": release.app_name, "version": release.version}

        if parsed.scheme not in ("http", "https"):
            raise FirmwareError(
                f"Refusing firmware download over unsupported scheme"
                f" '{parsed.scheme}'",
                details,
            )

        host = _normalise_host(parsed.hostname or "")
        if not host:
            raise FirmwareError(
                "Refusing firmware download from a URL with no host", details
            )

        if not self._allowed_download_hosts:
            return

        if not any(
            host == allowed or host.endswith(f".{allowed}")
            for allowed in self._allowed_download_hosts
        ):
            raise FirmwareError(
                f"Refusing firmware download from untrusted host '{host}'",
                details,
            )


def _normalise_host(value: str) -> str:
    """A bare lowercase hostname, however the entry or URL spelled it.

    Accepts the shapes an operator reasonably writes in the allow list, and
    matches the trailing dot of an absolute name against the same entry.
    """
    host = value.strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0].split("@")[-1]
    if host.startswith("*."):
        host = host[2:]
    return host.split(":", 1)[0].strip(".") if "]" not in host else host.strip(".")


def _is_safe_app_name(value: str) -> bool:
    """Whether the name is safe as a URL path segment.

    "." and ".." satisfy the character class but resolve to a different index
    path once the URL is normalized.
    """
    return value not in (".", "..") and bool(_SAFE_APP_NAME.fullmatch(value))


def _redirect_target(response: httpx.Response, release: FirmwareRelease) -> str:
    """The absolute address a redirect points at."""
    location = response.headers.get("location", "").strip()
    if not location:
        raise FirmwareError(
            f"Firmware download for {release.app_name} {release.version}"
            f" was redirected without a target",
            {"app_name": release.app_name, "version": release.version},
        )
    return str(response.url.join(location))


def _reject_compressed(response: httpx.Response, release: FirmwareRelease) -> None:
    """Refuse a body the client would have to decompress to read.

    Firmware bundles are already zips, so a content encoding here is either a
    broken server or an attempt to expand a small body into a large one.
    """
    encoding = response.headers.get("content-encoding", "").strip().lower()
    if encoding and encoding != "identity":
        raise FirmwareError(
            f"Firmware download for {release.app_name} {release.version}"
            f" arrived with unsupported content encoding '{encoding}'",
            {"app_name": release.app_name, "version": release.version},
        )


def _reject_oversized(response: httpx.Response, release: FirmwareRelease) -> None:
    """Refuse a body whose declared length already exceeds the cap."""
    declared = response.headers.get("content-length", "")
    if declared.isdigit() and int(declared) > _MAX_BUNDLE_SIZE_BYTES:
        raise FirmwareError(
            f"Firmware download for {release.app_name} {release.version}"
            f" declares {declared} bytes, over the"
            f" {_MAX_BUNDLE_SIZE_BYTES} byte limit",
            {"app_name": release.app_name, "version": release.version},
        )


def _release_from_index_entry(
    app_name: str, data: Any, channel: str
) -> FirmwareRelease | None:
    if not isinstance(data, dict):
        return None
    entry = data.get(channel)
    if not isinstance(entry, dict):
        return None

    version = entry.get("version")
    build_id = entry.get("build_id")
    download_url = entry.get("url")
    if not (
        isinstance(version, str)
        and version
        and isinstance(build_id, str)
        and build_id
        and isinstance(download_url, str)
        and download_url
    ):
        return None

    return FirmwareRelease(
        app_name=app_name,
        version=version,
        build_id=build_id,
        download_url=download_url,
        channel=channel,
    )
