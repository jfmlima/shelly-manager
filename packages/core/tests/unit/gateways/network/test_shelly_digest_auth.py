import httpx
import pytest
from core.gateways.network.shelly_digest_auth import ShellyDigestAuth


class TestShellyDigestAuth:

    def _run_auth_flow(
        self, auth: ShellyDigestAuth, www_authenticate: str
    ) -> httpx.Request:
        """Drive auth_flow through a 401 challenge and return the authenticated request."""
        request = httpx.Request("POST", "http://192.168.1.100/rpc")
        flow = auth.auth_flow(request)

        # First yield: initial probe (no auth header yet)
        probe_request = next(flow)
        assert "Authorization" not in probe_request.headers

        # Simulate 401 challenge
        response = httpx.Response(
            401,
            headers={"www-authenticate": www_authenticate},
            request=probe_request,
        )

        # Second yield: authenticated request
        try:
            auth_request = flow.send(response)
        except StopIteration:
            pytest.fail("auth_flow did not yield an authenticated request")

        assert "Authorization" in auth_request.headers
        return auth_request

    def test_it_includes_empty_opaque(self):
        auth = ShellyDigestAuth(username="admin", password="secret")
        challenge = (
            'Digest realm="ShellyWallDisplay-000822891495", '
            'qop="auth", nonce="0b00ddda", opaque="", algorithm=SHA-256'
        )
        request = self._run_auth_flow(auth, challenge)
        header = request.headers["Authorization"]

        assert 'opaque=""' in header

    def test_it_includes_nonempty_opaque(self):
        auth = ShellyDigestAuth(username="admin", password="secret")
        challenge = (
            'Digest realm="shellypro4pm-f008d1d8b8b8", '
            'qop="auth", nonce="abc123", opaque="xyz789", algorithm=SHA-256'
        )
        request = self._run_auth_flow(auth, challenge)
        header = request.headers["Authorization"]

        assert 'opaque="xyz789"' in header

    def test_it_omits_missing_opaque(self):
        auth = ShellyDigestAuth(username="admin", password="secret")
        challenge = (
            'Digest realm="shellypro4pm-f008d1d8b8b8", '
            'qop="auth", nonce="abc123", algorithm=SHA-256'
        )
        request = self._run_auth_flow(auth, challenge)
        header = request.headers["Authorization"]

        assert "opaque" not in header

    def test_it_produces_valid_sha256_digest(self):
        auth = ShellyDigestAuth(username="admin", password="pass123")
        challenge = (
            'Digest realm="ShellyWallDisplay-000822891495", '
            'qop="auth", nonce="0b00ddda", opaque="", algorithm=SHA-256'
        )
        request = self._run_auth_flow(auth, challenge)
        header = request.headers["Authorization"]

        assert header.startswith("Digest ")
        assert "algorithm=SHA-256" in header
        assert 'realm="ShellyWallDisplay-000822891495"' in header
        assert 'nonce="0b00ddda"' in header
        assert "response=" in header
        assert "nc=" in header
        assert "cnonce=" in header

    def test_it_supports_md5_algorithm(self):
        auth = ShellyDigestAuth(username="admin", password="pass123")
        challenge = (
            'Digest realm="shelly1-abc", '
            'qop="auth", nonce="def456", algorithm=MD5'
        )
        request = self._run_auth_flow(auth, challenge)
        header = request.headers["Authorization"]

        assert header.startswith("Digest ")
        assert "algorithm=MD5" in header

    def test_it_reuses_cached_challenge_on_subsequent_requests(self):
        auth = ShellyDigestAuth(username="admin", password="secret")
        challenge = (
            'Digest realm="ShellyWallDisplay-000822891495", '
            'qop="auth", nonce="0b00ddda", opaque="", algorithm=SHA-256'
        )

        # First flow: goes through 401 challenge
        self._run_auth_flow(auth, challenge)

        # Second flow: should use cached challenge (no 401 needed)
        request2 = httpx.Request("POST", "http://192.168.1.100/rpc")
        flow2 = auth.auth_flow(request2)

        first_yield = next(flow2)
        assert "Authorization" in first_yield.headers
        assert 'opaque=""' in first_yield.headers["Authorization"]
