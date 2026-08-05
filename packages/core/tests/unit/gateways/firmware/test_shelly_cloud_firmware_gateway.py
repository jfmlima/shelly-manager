"""Tests for the Shelly cloud firmware gateway."""

import asyncio
import hashlib

import httpx
import pytest
from core.domain.entities.exceptions import FirmwareError
from core.domain.value_objects.firmware_release import FirmwareRelease
from core.gateways.firmware import ShellyCloudFirmwareGateway

INDEX_URL = "https://updates.example.test/update"


def _gateway(handler):
    transport = httpx.MockTransport(handler)
    return ShellyCloudFirmwareGateway(
        index_url=INDEX_URL, session=httpx.AsyncClient(transport=transport)
    )


def _release(**kwargs):
    base = {
        "app_name": "Plus2PM",
        "version": "1.7.5",
        "build_id": "20250611-100000/1.7.5-g1234567",
        "download_url": "https://fwcdn.shelly.cloud/Plus2PM.zip",
        "channel": "stable",
    }
    base.update(kwargs)
    return FirmwareRelease(**base)


class TestGetLatest:
    async def test_it_returns_the_stable_release(self):
        def handler(request):
            assert request.url == httpx.URL(f"{INDEX_URL}/Plus2PM")
            return httpx.Response(
                200,
                json={
                    "name": "Shelly Plus 2PM",
                    "stable": {
                        "version": "1.7.5",
                        "build_id": "20250611-100000/1.7.5-g1234567",
                        "url": "https://fwcdn.example.test/Plus2PM.zip",
                    },
                },
            )

        release = await _gateway(handler).get_latest("Plus2PM")

        assert release is not None
        assert release.app_name == "Plus2PM"
        assert release.version == "1.7.5"
        assert release.build_id == "20250611-100000/1.7.5-g1234567"
        assert release.download_url == "https://fwcdn.example.test/Plus2PM.zip"
        assert release.channel == "stable"

    async def test_it_returns_the_beta_release_when_asked(self):
        def handler(request):
            return httpx.Response(
                200,
                json={
                    "stable": {
                        "version": "1.7.5",
                        "build_id": "20250611-100000/1.7.5-g1234567",
                        "url": "https://fwcdn.example.test/Plus2PM.zip",
                    },
                    "beta": {
                        "version": "1.8.0-beta2",
                        "build_id": "20250701-100000/1.8.0-beta2-g89abcde",
                        "url": "https://fwcdn.example.test/Plus2PM-beta.zip",
                    },
                },
            )

        release = await _gateway(handler).get_latest("Plus2PM", "beta")

        assert release is not None
        assert release.version == "1.8.0-beta2"
        assert release.build_id == "20250701-100000/1.8.0-beta2-g89abcde"
        assert release.channel == "beta"

    async def test_it_returns_none_when_the_channel_has_no_entry(self):
        def handler(request):
            return httpx.Response(
                200,
                json={
                    "stable": {
                        "version": "1.7.5",
                        "build_id": "20250611-100000/1.7.5-g1234567",
                        "url": "https://fwcdn.example.test/Plus2PM.zip",
                    }
                },
            )

        assert (await _gateway(handler).get_latest("Plus2PM", "beta")) is None

    async def test_it_returns_none_when_the_index_has_no_entry(self):
        def handler(request):
            return httpx.Response(404)

        assert (await _gateway(handler).get_latest("Unknown")) is None

    async def test_it_returns_none_without_a_stable_block(self):
        def handler(request):
            return httpx.Response(200, json={"name": "Shelly Plus 2PM"})

        assert (await _gateway(handler).get_latest("Plus2PM")) is None

    async def test_it_returns_none_when_the_stable_block_is_incomplete(self):
        def handler(request):
            return httpx.Response(200, json={"stable": {"version": "1.7.5"}})

        assert (await _gateway(handler).get_latest("Plus2PM")) is None

    async def test_it_returns_none_for_non_string_metadata(self):
        def handler(request):
            return httpx.Response(
                200,
                json={
                    "stable": {
                        "version": {"unexpected": "object"},
                        "build_id": "x",
                        "url": "https://fwcdn.example.test/x.zip",
                    }
                },
            )

        assert (await _gateway(handler).get_latest("Plus2PM")) is None

    async def test_it_raises_a_firmware_error_when_the_index_is_unreachable(self):
        def handler(request):
            raise httpx.ConnectError("connection refused")

        with pytest.raises(FirmwareError, match="index request failed"):
            await _gateway(handler).get_latest("Plus2PM")

    async def test_it_raises_a_firmware_error_on_a_server_error(self):
        def handler(request):
            return httpx.Response(500)

        with pytest.raises(FirmwareError, match="index request failed"):
            await _gateway(handler).get_latest("Plus2PM")

    async def test_it_raises_a_firmware_error_on_an_unparseable_response(self):
        def handler(request):
            return httpx.Response(200, content=b"not json")

        with pytest.raises(FirmwareError, match="index request failed"):
            await _gateway(handler).get_latest("Plus2PM")

    async def test_it_refuses_an_unsafe_app_name(self):
        def handler(request):
            raise AssertionError("no request should be made")

        with pytest.raises(FirmwareError, match="unsafe app name"):
            await _gateway(handler).get_latest("Plus2PM/../evil")

    @pytest.mark.parametrize("app_name", [".", ".."])
    async def test_it_refuses_dot_segment_app_names(self, app_name):
        def handler(request):
            raise AssertionError("no request should be made")

        with pytest.raises(FirmwareError, match="unsafe app name"):
            await _gateway(handler).get_latest(app_name)


class TestDownload:
    async def test_it_streams_the_bundle_and_reports_size_and_sha256(self, tmp_path):
        payload = b"zip-bytes" * 1000

        def handler(request):
            assert request.url == httpx.URL("https://fwcdn.shelly.cloud/Plus2PM.zip")
            return httpx.Response(200, content=payload)

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        size, sha256 = await _gateway(handler).download(_release(), str(dest))

        assert dest.read_bytes() == payload
        assert size == len(payload)
        assert sha256 == hashlib.sha256(payload).hexdigest()
        assert list(tmp_path.glob("*.part")) == []

    async def test_it_cleans_up_the_partial_file_when_the_download_fails(
        self, tmp_path
    ):
        def handler(request):
            return httpx.Response(500)

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="download failed"):
            await _gateway(handler).download(_release(), str(dest))

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []

    async def test_it_wraps_a_disk_error_in_a_firmware_error(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"zip-bytes")

        dest = tmp_path / "missing-dir" / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="download failed"):
            await _gateway(handler).download(_release(), str(dest))

        assert list(tmp_path.rglob("*.part")) == []

    async def test_it_cleans_up_the_partial_file_when_cancelled(self, tmp_path):
        first_chunk_sent = asyncio.Event()
        never = asyncio.Event()

        class StallingStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                yield b"zip-bytes"
                first_chunk_sent.set()
                await never.wait()
                yield b"more"

        def handler(request):
            return httpx.Response(200, stream=StallingStream())

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        task = asyncio.create_task(_gateway(handler).download(_release(), str(dest)))
        await first_chunk_sent.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []

    @pytest.mark.parametrize(
        "download_url",
        [
            "http://127.0.0.1:9200/_search",
            "http://192.168.40.10/admin",
            "https://attacker.example.test/Plus2PM.zip",
            "file:///etc/passwd",
        ],
    )
    async def test_it_refuses_a_download_outside_the_allowed_hosts(
        self, tmp_path, download_url
    ):
        def handler(request):
            raise AssertionError("no request should be made")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        with pytest.raises(FirmwareError, match="Refusing firmware download"):
            await gateway.download(_release(download_url=download_url), str(dest))

        assert not dest.exists()

    async def test_it_refuses_a_redirect_off_the_allowed_hosts(self, tmp_path):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            if request.url.host == "fwcdn.shelly.cloud":
                return httpx.Response(
                    302, headers={"Location": "http://127.0.0.1:9200/_search"}
                )
            return httpx.Response(200, content=b"INTERNAL-SECRET-BODY")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        with pytest.raises(FirmwareError, match="untrusted host '127.0.0.1'"):
            await gateway.download(_release(), str(dest))

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []
        assert not any("127.0.0.1" in url for url in seen)

    async def test_it_follows_a_redirect_that_stays_on_an_allowed_host(self, tmp_path):
        def handler(request):
            if request.url.path == "/redirect":
                return httpx.Response(
                    302, headers={"Location": "https://fwcdn.shelly.cloud/real.zip"}
                )
            return httpx.Response(200, content=b"zip")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        size, _ = await gateway.download(
            _release(download_url="https://updates.shelly.cloud/redirect"), str(dest)
        )

        assert size == 3
        assert dest.read_bytes() == b"zip"

    async def test_it_stops_a_redirect_loop(self, tmp_path):
        def handler(request):
            return httpx.Response(
                302, headers={"Location": "https://fwcdn.shelly.cloud/again"}
            )

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        with pytest.raises(FirmwareError, match="redirected more than"):
            await gateway.download(_release(), str(dest))

        assert list(tmp_path.glob("*.part")) == []

    @pytest.mark.parametrize(
        "entry",
        ["shelly.cloud", "*.shelly.cloud", "SHELLY.CLOUD:443", "https://shelly.cloud"],
    )
    async def test_it_reads_the_allow_list_however_it_is_written(self, tmp_path, entry):
        def handler(request):
            return httpx.Response(200, content=b"zip")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=[entry],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        size, _ = await gateway.download(_release(), str(dest))

        assert size == 3

    async def test_it_allows_an_absolute_form_of_the_host(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"zip")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        size, _ = await gateway.download(
            _release(download_url="https://fwcdn.shelly.cloud./Plus2PM.zip"), str(dest)
        )

        assert size == 3

    async def test_it_refuses_an_empty_bundle(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"")

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="was empty"):
            await _gateway(handler).download(_release(), str(dest))

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []

    @pytest.mark.parametrize(
        "download_url",
        [
            "https://fwcdn.shelly.cloud/" + "x" * 70000,
            "https://xn--a.shelly.cloud/x.zip",
        ],
    )
    async def test_it_wraps_an_unusable_url_in_a_firmware_error(
        self, tmp_path, download_url
    ):
        def handler(request):
            return httpx.Response(200, content=b"zip")

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="download failed"):
            await _gateway(handler).download(
                _release(download_url=download_url), str(dest)
            )

        assert list(tmp_path.glob("*.part")) == []

    async def test_it_allows_a_subdomain_of_an_allowed_host(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"zip")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=["shelly.cloud"],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        size, _ = await gateway.download(
            _release(download_url="https://fwcdn.shelly.cloud/Plus2PM.zip"), str(dest)
        )

        assert size == 3

    async def test_it_allows_any_host_when_the_allow_list_is_empty(self, tmp_path):
        def handler(request):
            return httpx.Response(200, content=b"zip")

        gateway = ShellyCloudFirmwareGateway(
            index_url=INDEX_URL,
            session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
            allowed_download_hosts=[],
        )
        dest = tmp_path / "Plus2PM-1.7.5.zip"

        size, _ = await gateway.download(
            _release(download_url="https://mirror.example.test/Plus2PM.zip"), str(dest)
        )

        assert size == 3

    async def test_it_rejects_a_compressed_body(self, tmp_path):
        class GzipStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                raise AssertionError("body must not be read")
                yield b""

        def handler(request):
            return httpx.Response(
                200,
                stream=GzipStream(),
                headers={"Content-Encoding": "gzip"},
            )

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="content encoding"):
            await _gateway(handler).download(_release(), str(dest))

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []

    async def test_it_rejects_a_declared_length_over_the_cap(
        self, tmp_path, monkeypatch
    ):
        from core.gateways.firmware import shelly_cloud_firmware_gateway

        monkeypatch.setattr(shelly_cloud_firmware_gateway, "_MAX_BUNDLE_SIZE_BYTES", 10)

        def handler(request):
            return httpx.Response(200, content=b"zip-bytes" * 10)

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="over the"):
            await _gateway(handler).download(_release(), str(dest))

        assert not dest.exists()

    async def test_it_rejects_a_bundle_over_the_size_cap(self, tmp_path, monkeypatch):
        from core.gateways.firmware import shelly_cloud_firmware_gateway

        monkeypatch.setattr(shelly_cloud_firmware_gateway, "_MAX_BUNDLE_SIZE_BYTES", 10)

        class UndeclaredLengthStream(httpx.AsyncByteStream):
            async def __aiter__(self):
                for _ in range(5):
                    yield b"zip-bytes"

        def handler(request):
            return httpx.Response(200, stream=UndeclaredLengthStream())

        dest = tmp_path / "Plus2PM-1.7.5.zip"
        with pytest.raises(FirmwareError, match="exceeded"):
            await _gateway(handler).download(_release(), str(dest))

        assert not dest.exists()
        assert list(tmp_path.glob("*.part")) == []
