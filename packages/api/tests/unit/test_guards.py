import core.settings
import pytest
from api.guards.auth import require_auth
from litestar.exceptions import NotAuthorizedException
from litestar.testing import RequestFactory


def _connection(authorization: str | None = None):
    headers = {"Authorization": authorization} if authorization else {}
    return RequestFactory().get("/", headers=headers)


class TestRequireAuth:

    def test_it_allows_the_request_when_auth_is_disabled(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", None)

        require_auth(_connection(), None)

    def test_it_rejects_a_missing_header_when_auth_is_enabled(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with pytest.raises(NotAuthorizedException):
            require_auth(_connection(), None)

    def test_it_rejects_a_malformed_header(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with pytest.raises(NotAuthorizedException):
            require_auth(_connection(authorization="secret123"), None)

    def test_it_rejects_the_wrong_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with pytest.raises(NotAuthorizedException):
            require_auth(_connection(authorization="Bearer wrong"), None)

    def test_it_rejects_a_non_ascii_token_without_erroring(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with pytest.raises(NotAuthorizedException):
            require_auth(_connection(authorization="Bearer nöt-ascii"), None)

    def test_its_rejection_carries_the_www_authenticate_header(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        with pytest.raises(NotAuthorizedException) as exc_info:
            require_auth(_connection(), None)

        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

    def test_it_allows_the_correct_token(self, monkeypatch):
        monkeypatch.setattr(core.settings.settings, "auth_token", "secret123")

        require_auth(_connection(authorization="Bearer secret123"), None)
