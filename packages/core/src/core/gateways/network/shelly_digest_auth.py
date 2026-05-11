"""
Shelly-specific DigestAuth that correctly handles empty opaque values.

httpx 0.28.1's DigestAuth uses ``if challenge.opaque:`` which treats b""
as falsy, omitting opaque from the Authorization header. RFC 7616 requires
clients to return opaque unchanged — even when empty. Shelly Wall Display
devices send ``opaque=""`` and reject responses that omit it.
"""

from __future__ import annotations

import httpx
from httpx._auth import _DigestAuthChallenge
from httpx._models import Request
from httpx._utils import to_str


class ShellyDigestAuth(httpx.DigestAuth):
    # Pinned to httpx 0.28.1 — verify on upgrades.
    def _build_auth_header(
        self, request: Request, challenge: _DigestAuthChallenge
    ) -> str:
        hash_func = self._ALGORITHM_TO_HASH_FUNCTION[challenge.algorithm.upper()]

        def digest(data: bytes) -> bytes:
            return hash_func(data).hexdigest().encode()

        A1 = b":".join((self._username, challenge.realm, self._password))

        path = request.url.raw_path
        A2 = b":".join((request.method.encode(), path))
        HA2 = digest(A2)

        nc_value = b"%08x" % self._nonce_count
        cnonce = self._get_client_nonce(self._nonce_count, challenge.nonce)
        self._nonce_count += 1

        HA1 = digest(A1)
        if challenge.algorithm.lower().endswith("-sess"):
            HA1 = digest(b":".join((HA1, challenge.nonce, cnonce)))

        qop = self._resolve_qop(challenge.qop, request=request)
        if qop is None:
            digest_data = [HA1, challenge.nonce, HA2]
        else:
            digest_data = [HA1, challenge.nonce, nc_value, cnonce, qop, HA2]

        format_args: dict[str, bytes] = {
            "username": self._username,
            "realm": challenge.realm,
            "nonce": challenge.nonce,
            "uri": path,
            "response": digest(b":".join(digest_data)),
            "algorithm": challenge.algorithm.encode(),
        }
        if challenge.opaque is not None:
            format_args["opaque"] = challenge.opaque
        if qop:
            format_args["qop"] = b"auth"
            format_args["nc"] = nc_value
            format_args["cnonce"] = cnonce

        return "Digest " + self._get_header_value(format_args)

    def _get_header_value(self, header_fields: dict[str, bytes]) -> str:
        NON_QUOTED_FIELDS = ("algorithm", "qop", "nc")
        QUOTED_TEMPLATE = '{}="{}"'
        NON_QUOTED_TEMPLATE = "{}={}"

        header_value = ""
        for i, (field, value) in enumerate(header_fields.items()):
            if i > 0:
                header_value += ", "
            template = (
                QUOTED_TEMPLATE
                if field not in NON_QUOTED_FIELDS
                else NON_QUOTED_TEMPLATE
            )
            header_value += template.format(field, to_str(value))

        return header_value
