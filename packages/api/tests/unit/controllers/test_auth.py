import core.settings
from api.controllers.auth import auth_router
from api.presentation.handlers import EXCEPTION_HANDLERS
from litestar.testing import create_test_client


class TestAuthController:

    def test_config_reports_disabled_when_no_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", None)

        with create_test_client(route_handlers=[auth_router]) as client:
            response = client.get("/auth/config")

            assert response.status_code == 200
            assert response.json() == {"enabled": False}

    def test_config_reports_enabled_when_a_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with create_test_client(route_handlers=[auth_router]) as client:
            response = client.get("/auth/config")

            assert response.status_code == 200
            assert response.json() == {"enabled": True}

    def test_config_needs_no_header_even_when_a_token_is_set(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with create_test_client(route_handlers=[auth_router]) as client:
            response = client.get("/auth/config")

            assert response.status_code == 200

    def test_verify_passes_through_when_auth_is_disabled(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", None)

        with create_test_client(route_handlers=[auth_router]) as client:
            response = client.get("/auth/verify")

            assert response.status_code == 200
            assert response.json() == {"valid": True}

    def test_verify_rejects_a_missing_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with create_test_client(
            route_handlers=[auth_router], exception_handlers=EXCEPTION_HANDLERS
        ) as client:
            response = client.get("/auth/verify")

            assert response.status_code == 401
            assert response.json()["error"] == "Unauthorized"

    def test_verify_rejects_the_wrong_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with create_test_client(
            route_handlers=[auth_router], exception_handlers=EXCEPTION_HANDLERS
        ) as client:
            response = client.get(
                "/auth/verify", headers={"Authorization": "Bearer wrong"}
            )

            assert response.status_code == 401

    def test_verify_accepts_the_correct_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with create_test_client(route_handlers=[auth_router]) as client:
            response = client.get(
                "/auth/verify", headers={"Authorization": "Bearer secret123"}
            )

            assert response.status_code == 200
            assert response.json() == {"valid": True}

    def test_it_is_mounted_on_the_app(self, app):
        assert any(route.path == "/api/auth/config" for route in app.routes)
        assert any(route.path == "/api/auth/verify" for route in app.routes)
