"""Tests for APDeviceDetector."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from core.domain.entities.exceptions import (
    DeviceCommunicationError,
    DeviceNotFoundError,
)
from core.gateways.device.ap_device_detector import APDeviceDetector


class TestAPDeviceDetector:
    @pytest.fixture
    def detector(self):
        return APDeviceDetector(timeout=5.0)

    @pytest.fixture
    def gen2_response_data(self):
        return {
            "id": "shellyplus2pm-a8032ab636ec",
            "mac": "A8032AB636EC",
            "model": "SNSW-102P16EU",
            "gen": 2,
            "fw_id": "20230913-114010/1.0.0-abc123",
            "ver": "1.0.0",
            "app": "Plus2PM",
            "auth_en": False,
            "auth_domain": "shellyplus2pm-a8032ab636ec",
        }

    @pytest.fixture
    def gen1_response_data(self):
        return {
            "type": "SHSW-25",
            "mac": "AABBCCDDEEFF",
            "auth": False,
            "fw": "20211109-130434/v1.11.8-g8c7bb8d",
        }

    async def test_it_detects_gen2_device(self, detector, gen2_response_data):
        mock_response = httpx.Response(
            200,
            content=json.dumps(gen2_response_data).encode(),
            request=httpx.Request("GET", "http://192.168.33.1/shelly"),
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            info = await detector.detect("192.168.33.1")

        assert info.device_id == "shellyplus2pm-a8032ab636ec"
        assert info.mac == "A8032AB636EC"
        assert info.model == "SNSW-102P16EU"
        assert info.generation == 2
        assert info.firmware_version == "1.0.0"
        assert info.auth_enabled is False
        assert info.app == "Plus2PM"

    async def test_it_rejects_gen1_device(self, detector, gen1_response_data):
        mock_response = httpx.Response(
            200,
            content=json.dumps(gen1_response_data).encode(),
            request=httpx.Request("GET", "http://192.168.33.1/shelly"),
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(DeviceNotFoundError) as exc_info:
                await detector.detect("192.168.33.1")

            assert "Gen1" in str(exc_info.value)

    async def test_it_raises_on_timeout(self, detector):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("timed out")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(DeviceNotFoundError):
                await detector.detect("192.168.33.1")

    async def test_it_raises_on_connection_error(self, detector):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.ConnectError("refused")
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(DeviceCommunicationError):
                await detector.detect("192.168.33.1")

    async def test_it_raises_on_non_200_response(self, detector):
        mock_response = httpx.Response(
            500,
            content=b"Internal Server Error",
            request=httpx.Request("GET", "http://192.168.33.1/shelly"),
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(DeviceCommunicationError):
                await detector.detect("192.168.33.1")

    async def test_it_normalizes_mac_address(self, detector):
        data = {
            "id": "shellytest-aabbccddeeff",
            "mac": "aa:bb:cc:dd:ee:ff",
            "model": "TEST",
            "gen": 3,
            "fw_id": "test",
            "ver": "1.0.0",
            "auth_en": True,
            "auth_domain": "shellytest-aabbccddeeff",
        }

        mock_response = httpx.Response(
            200,
            content=json.dumps(data).encode(),
            request=httpx.Request("GET", "http://192.168.33.1/shelly"),
        )

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            info = await detector.detect("192.168.33.1")

        assert info.mac == "AABBCCDDEEFF"
        assert info.generation == 3
        assert info.auth_enabled is True
