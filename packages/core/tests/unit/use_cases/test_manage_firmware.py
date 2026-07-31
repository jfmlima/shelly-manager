"""Tests for the manage firmware use case."""

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.settings import FirmwareSettings
from core.use_cases.manage_firmware import ManageFirmware


def _bundle(bundle_id=7, file_name="Plus2PM-1.7.5.zip"):
    return FirmwareBundle(
        id=bundle_id,
        app_name="Plus2PM",
        version="1.7.5",
        build_id="20250611-100000/1.7.5-g1234567",
        file_name=file_name,
    )


class TestManageFirmware:
    @pytest.fixture
    def mock_repository(self):
        repository = AsyncMock()
        repository.get = AsyncMock(return_value=_bundle())
        repository.delete = AsyncMock(return_value=True)
        repository.list = AsyncMock(return_value=[_bundle()])
        return repository

    @pytest.fixture
    def use_case(self, mock_repository, tmp_path):
        @asynccontextmanager
        async def repository_factory():
            yield mock_repository

        return ManageFirmware(
            repository_factory=repository_factory,
            settings=FirmwareSettings(dir=str(tmp_path)),
        )

    async def test_it_lists_bundles(self, use_case):
        bundles = await use_case.list_bundles()

        assert len(bundles) == 1
        assert bundles[0].app_name == "Plus2PM"

    async def test_it_deletes_the_bundle_and_its_file(
        self, use_case, mock_repository, tmp_path
    ):
        zip_path = tmp_path / "Plus2PM-1.7.5.zip"
        zip_path.write_bytes(b"zip")

        assert (await use_case.delete_bundle(7)) is True

        mock_repository.delete.assert_awaited_once_with(7)
        assert not zip_path.exists()

    async def test_it_returns_false_for_a_missing_bundle(
        self, use_case, mock_repository
    ):
        mock_repository.get = AsyncMock(return_value=None)

        assert (await use_case.delete_bundle(7)) is False
        mock_repository.delete.assert_not_awaited()

    async def test_it_keeps_a_hostile_file_name_inside_the_store(
        self, use_case, tmp_path
    ):
        path = use_case.bundle_path(_bundle(file_name="../evil.zip"))

        assert path == str(tmp_path / "evil.zip")
