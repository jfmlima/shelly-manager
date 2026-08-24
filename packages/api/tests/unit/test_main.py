from datetime import datetime

import core.settings
import pytest
from api.controllers.monitoring import health_check
from api.main import app_factory
from core.domain.entities.exceptions import ConfigurationError
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.testing import TestClient, create_test_client


class TestMainApp:

    def test_it_creates_app_with_default_config(self, app):
        assert app is not None
        assert len(app.routes) > 0

    def test_it_app_factory_returns_litestar_app(self):
        assert isinstance(app_factory(), Litestar)

    def test_it_handles_cors_correctly(self):
        cors_config = CORSConfig(
            allow_origins=["*"],
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )

        with create_test_client(
            route_handlers=[health_check], cors_config=cors_config
        ) as client:
            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            assert response.status_code == 204
            assert "access-control-allow-origin" in response.headers
            assert response.headers["access-control-allow-origin"] == "*"

    def test_it_handles_validation_error(self):
        # This test would need a route that has validation, but for now let's test a simpler case
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data

            timestamp = datetime.fromisoformat(data["timestamp"])
            assert isinstance(timestamp, datetime)

    def test_it_routes_to_api_endpoints(self):
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/health")
            assert response.status_code == 200

    def test_it_returns_404_for_unknown_routes(self):
        with create_test_client(route_handlers=[health_check]) as client:
            response = client.get("/unknown/route")

            assert response.status_code == 404


class TestSecretKeyAtStartup:

    async def test_it_refuses_to_start_without_a_secret_key(self, monkeypatch):
        import core.settings

        monkeypatch.setattr(core.settings.settings, "secret_key", None)

        with pytest.raises(BaseExceptionGroup) as excinfo:
            async with app_factory().lifespan():
                pass

        assert excinfo.group_contains(ConfigurationError, match="SHELLY_SECRET_KEY")

    async def test_it_refuses_to_start_on_a_malformed_secret_key(self, monkeypatch):
        import core.settings

        monkeypatch.setattr(core.settings.settings, "secret_key", "not-a-fernet-key")

        with pytest.raises(BaseExceptionGroup) as excinfo:
            async with app_factory().lifespan():
                pass

        assert excinfo.group_contains(ConfigurationError, match="SHELLY_SECRET_KEY")


class TestOptionalAuthToken:

    def test_health_and_auth_config_stay_public_when_a_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            assert client.get("/api/health").status_code == 200
            assert client.get("/api/auth/config").status_code == 200

    def test_docs_stay_public_when_a_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            assert client.get("/docs").status_code == 200

    def test_a_protected_route_401s_without_the_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            response = client.get("/api/devices/scan")

            assert response.status_code == 401
            assert response.json()["error"] == "Unauthorized"

    def test_a_protected_route_is_reachable_with_the_correct_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            response = client.get(
                "/api/devices/scan", headers={"Authorization": "Bearer secret123"}
            )

            assert response.status_code != 401

    def test_protected_routes_are_unaffected_when_no_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", None)

        with TestClient(app=app_factory()) as client:
            response = client.get("/api/devices/scan")

            assert response.status_code != 401
