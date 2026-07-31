"""Tests for the acquire firmware use case."""

import asyncio
import hashlib
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.exceptions import FirmwareError
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.settings import FirmwareSettings
from core.use_cases.acquire_firmware import AcquireFirmware


def _build_id(version="1.7.5"):
    return f"20250611-100000/{version}-g1234567"


def _release(version="1.7.5"):
    return FirmwareRelease(
        app_name="Plus2PM",
        version=version,
        build_id=_build_id(version),
        download_url="https://fwcdn.example.test/Plus2PM.zip",
        channel="stable",
    )


def _expected_file_name(version="1.7.5"):
    identity = "\0".join(("Plus2PM", version, _build_id(version)))
    digest = hashlib.sha256(identity.encode()).hexdigest()[:16]
    return f"Plus2PM-{version}-{digest}.zip"


def _bundle(version="1.7.5", bundle_id=7):
    return FirmwareBundle(
        id=bundle_id,
        app_name="Plus2PM",
        version=version,
        build_id=f"20250611-100000/{version}-g1234567",
        file_name=f"Plus2PM-{version}.zip",
        size_bytes=2048,
        sha256="ab" * 32,
    )


class TestAcquireFirmware:
    @pytest.fixture
    def mock_firmware_gateway(self):
        gateway = AsyncMock()
        gateway.get_latest = AsyncMock(return_value=_release())
        gateway.download = AsyncMock(return_value=(2048, "ab" * 32))
        return gateway

    @pytest.fixture
    def mock_repository(self):
        repository = AsyncMock()
        repository.find = AsyncMock(return_value=None)
        repository.create = AsyncMock(side_effect=lambda bundle: bundle)
        return repository

    @pytest.fixture
    def use_case(self, mock_firmware_gateway, mock_repository, tmp_path):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        return AcquireFirmware(
            firmware_gateway=mock_firmware_gateway,
            repository_factory=repository_factory,
            settings=FirmwareSettings(dir=str(tmp_path)),
        )

    async def test_it_returns_the_cached_bundle_without_downloading(
        self, use_case, mock_firmware_gateway, mock_repository, tmp_path
    ):
        (tmp_path / "Plus2PM-1.7.5.zip").write_bytes(b"zip")
        cached = _bundle()
        mock_repository.find = AsyncMock(return_value=cached)

        result = await use_case.execute("Plus2PM")

        assert result is cached
        mock_repository.find.assert_awaited_once_with("Plus2PM", "1.7.5", _build_id())
        mock_firmware_gateway.download.assert_not_awaited()
        mock_repository.create.assert_not_awaited()

    async def test_it_restores_a_cached_bundle_whose_file_left_the_disk(
        self, use_case, mock_firmware_gateway, mock_repository, tmp_path
    ):
        cached = _bundle()
        mock_repository.find = AsyncMock(return_value=cached)

        result = await use_case.execute("Plus2PM")

        assert result is cached
        mock_firmware_gateway.download.assert_awaited_once_with(
            _release(), str(tmp_path / "Plus2PM-1.7.5.zip")
        )
        mock_repository.create.assert_not_awaited()

    async def test_it_downloads_and_stores_on_a_cache_miss(
        self, use_case, mock_firmware_gateway, mock_repository, tmp_path
    ):
        result = await use_case.execute("Plus2PM")

        mock_firmware_gateway.download.assert_awaited_once_with(
            _release(), str(tmp_path / _expected_file_name())
        )
        mock_repository.create.assert_awaited_once()
        assert result.app_name == "Plus2PM"
        assert result.version == "1.7.5"
        assert result.build_id == "20250611-100000/1.7.5-g1234567"
        assert result.file_name == _expected_file_name()
        assert result.size_bytes == 2048
        assert result.sha256 == "ab" * 32

    async def test_it_raises_when_the_index_has_no_release(
        self, use_case, mock_firmware_gateway
    ):
        mock_firmware_gateway.get_latest = AsyncMock(return_value=None)

        with pytest.raises(FirmwareError, match="No firmware published"):
            await use_case.execute("Unknown")

        mock_firmware_gateway.download.assert_not_awaited()

    async def test_it_refuses_an_unsafe_app_name(self, use_case, mock_firmware_gateway):
        with pytest.raises(FirmwareError, match="unsafe app name"):
            await use_case.execute("Plus2PM/../evil")

        mock_firmware_gateway.get_latest.assert_not_awaited()
        mock_firmware_gateway.download.assert_not_awaited()

    @pytest.mark.parametrize("app_name", [".", ".."])
    async def test_it_refuses_dot_segment_app_names(
        self, use_case, mock_firmware_gateway, app_name
    ):
        with pytest.raises(FirmwareError, match="unsafe app name"):
            await use_case.execute(app_name)

        mock_firmware_gateway.get_latest.assert_not_awaited()

    async def test_it_uses_a_supplied_release_without_re_querying_the_index(
        self, use_case, mock_firmware_gateway, mock_repository, tmp_path
    ):
        release = _release()

        result = await use_case.execute("Plus2PM", release)

        mock_firmware_gateway.get_latest.assert_not_awaited()
        mock_firmware_gateway.download.assert_awaited_once_with(
            release, str(tmp_path / _expected_file_name())
        )
        assert result.version == "1.7.5"

    async def test_it_refuses_an_unsafe_version_from_the_index(
        self, use_case, mock_firmware_gateway
    ):
        mock_firmware_gateway.get_latest = AsyncMock(
            return_value=_release(version="../../evil")
        )

        with pytest.raises(FirmwareError, match="unsafe firmware version"):
            await use_case.execute("Plus2PM")

        mock_firmware_gateway.download.assert_not_awaited()

    async def test_it_downloads_once_for_concurrent_requests(
        self, mock_firmware_gateway, tmp_path
    ):
        stored: dict[tuple[str, str, str], FirmwareBundle] = {}

        async def find(app_name, version, build_id):
            return stored.get((app_name, version, build_id))

        async def create(bundle):
            bundle.id = len(stored) + 1
            stored[(bundle.app_name, bundle.version, bundle.build_id)] = bundle
            return bundle

        async def download(release, dest_path):
            await asyncio.sleep(0)
            Path(dest_path).write_bytes(b"zip")
            return 2048, "ab" * 32

        repository = AsyncMock()
        repository.find = AsyncMock(side_effect=find)
        repository.create = AsyncMock(side_effect=create)
        mock_firmware_gateway.download = AsyncMock(side_effect=download)

        @asynccontextmanager
        async def repository_factory():
            yield repository

        use_case = AcquireFirmware(
            firmware_gateway=mock_firmware_gateway,
            repository_factory=repository_factory,
            settings=FirmwareSettings(dir=str(tmp_path)),
        )

        first, second = await asyncio.gather(
            use_case.execute("Plus2PM"), use_case.execute("Plus2PM")
        )

        assert first.id == second.id
        mock_firmware_gateway.download.assert_awaited_once()
        repository.create.assert_awaited_once()
