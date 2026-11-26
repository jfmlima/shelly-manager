import logging

import core.settings
import pytest
from api.main import app_factory
from core.domain.entities.exceptions import ConfigurationError
from litestar import Litestar
from litestar.testing import TestClient


class TestMainApp:

    def test_it_creates_app_with_default_config(self, app):
        assert app is not None
        assert len(app.routes) > 0

    def test_it_app_factory_returns_litestar_app(self):
        assert isinstance(app_factory(), Litestar)

    def test_it_lets_any_origin_call_the_api(self):
        with TestClient(app=app_factory()) as client:
            response = client.options(
                "/api/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

            assert response.status_code == 204
            assert response.headers["access-control-allow-origin"] == "*"

    def test_it_exposes_the_auth_challenge_to_a_cross_origin_web_ui(self):
        with TestClient(app=app_factory()) as client:
            response = client.get(
                "/api/health", headers={"Origin": "http://localhost:3000"}
            )

            exposed = response.headers["access-control-expose-headers"].lower()
            assert "www-authenticate" in exposed

    def test_it_returns_404_for_unknown_routes(self):
        with TestClient(app=app_factory()) as client:
            response = client.get("/unknown/route")

            assert response.status_code == 404


class TestLogLevel:

    @pytest.fixture(autouse=True)
    def reset_app_loggers(self):
        yield
        for name in ("core", "api"):
            logging.getLogger(name).setLevel(logging.NOTSET)

    def test_it_applies_the_configured_log_level_to_the_app_loggers(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings.logging, "level", "DEBUG")

        app = app_factory()

        assert logging.getLogger("core").getEffectiveLevel() == logging.DEBUG
        assert logging.getLogger("api").getEffectiveLevel() == logging.DEBUG
        assert app.logging_config.root["level"] == "INFO"
        assert "litestar" in app.logging_config.loggers

    def test_it_keeps_the_app_loggers_at_info_by_default(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings.logging, "level", "INFO")

        app_factory()

        assert logging.getLogger("core").getEffectiveLevel() == logging.INFO


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

    def test_firmware_download_stays_public_when_a_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            # 404 shows the handler ran and looked the bundle up; the guard did
            # not short-circuit it. The high id keeps the 404 reliable against
            # whatever the shared ./data database holds.
            response = client.get("/api/firmware/999999/download")

            assert response.status_code == 404

    def test_other_firmware_routes_stay_protected_when_a_token_is_set(
        self, monkeypatch
    ):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            for response in (
                client.get("/api/firmware/"),
                client.delete("/api/firmware/999999"),
            ):
                assert response.status_code == 401
                assert response.headers["www-authenticate"] == "Bearer"

    def test_a_protected_route_401s_without_the_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with TestClient(app=app_factory()) as client:
            response = client.get("/api/devices/scan")

            assert response.status_code == 401
            assert response.json()["error"] == "Unauthorized"
            assert response.headers["www-authenticate"] == "Bearer"

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
