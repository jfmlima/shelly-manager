from api.controllers.firmware import (
    delete_firmware,
    download_firmware,
    list_firmware,
)
from core.domain.entities.firmware_bundle import FirmwareBundle
from core.use_cases.manage_firmware import ManageFirmware
from litestar.di import Provide
from litestar.testing import create_test_client


def _bundle(bundle_id=7, file_name="Plus2PM-1.7.5.zip"):
    return FirmwareBundle(
        id=bundle_id,
        app_name="Plus2PM",
        version="1.7.5",
        build_id="20250611-100000/1.7.5-g1234567",
        file_name=file_name,
        size_bytes=2048,
        sha256="ab" * 32,
        downloaded_at=1753833600,
    )


def _client(route_handler, mock):
    return create_test_client(
        route_handlers=[route_handler],
        dependencies={
            "manage_firmware_use_case": Provide(lambda: mock, sync_to_thread=False)
        },
    )


class TestFirmwareController:
    def test_list_firmware_successfully(self):
        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def list_bundles(self):
                return [_bundle()]

        with _client(list_firmware, MockManageFirmware()) as client:
            response = client.get("/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 7
            assert data[0]["app_name"] == "Plus2PM"
            assert data[0]["version"] == "1.7.5"
            assert data[0]["file_name"] == "Plus2PM-1.7.5.zip"
            assert data[0]["size_bytes"] == 2048

    def test_delete_firmware_successfully(self):
        deleted = {}

        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def delete_bundle(self, bundle_id):
                deleted["id"] = bundle_id
                return True

        with _client(delete_firmware, MockManageFirmware()) as client:
            response = client.delete("/7")

            assert response.status_code == 204
            assert deleted["id"] == 7

    def test_delete_firmware_returns_404_for_a_missing_bundle(self):
        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def delete_bundle(self, bundle_id):
                return False

        with _client(delete_firmware, MockManageFirmware()) as client:
            response = client.delete("/7")

            assert response.status_code == 404

    def test_download_firmware_serves_the_zip(self, tmp_path):
        payload = b"zip-bytes" * 100
        zip_path = tmp_path / "Plus2PM-1.7.5.zip"
        zip_path.write_bytes(payload)

        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def get_bundle(self, bundle_id):
                return _bundle(bundle_id=bundle_id)

            def bundle_path(self, bundle):
                return str(zip_path)

        with _client(download_firmware, MockManageFirmware()) as client:
            response = client.get("/7/download")

            assert response.status_code == 200
            assert response.content == payload
            assert response.headers["content-type"] == "application/zip"
            assert "Plus2PM-1.7.5.zip" in response.headers["content-disposition"]

    def test_download_firmware_returns_404_for_a_missing_bundle(self):
        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def get_bundle(self, bundle_id):
                return None

        with _client(download_firmware, MockManageFirmware()) as client:
            response = client.get("/7/download")

            assert response.status_code == 404

    def test_download_firmware_returns_404_when_the_file_is_gone(self, tmp_path):
        class MockManageFirmware(ManageFirmware):
            def __init__(self):
                pass

            async def get_bundle(self, bundle_id):
                return _bundle(bundle_id=bundle_id)

            def bundle_path(self, bundle):
                return str(tmp_path / "missing.zip")

        with _client(download_firmware, MockManageFirmware()) as client:
            response = client.get("/7/download")

            assert response.status_code == 404
