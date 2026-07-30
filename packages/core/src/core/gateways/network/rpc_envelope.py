"""Reading a Shelly JSON-RPC response frame.

A device answers every ``/rpc`` call with HTTP 200 and a JSON-RPC frame:
``{"id": ..., "src": ..., "result": {...}}`` when the call worked, and the same
frame carrying ``"error"`` instead when it did not. Neither the payload nor the
failure is visible unless the frame is opened, so reading the frame as if it
were the payload turns device rejections into successes and stores envelopes
wherever the payload belongs.
"""

from typing import Any


class RpcError(Exception):
    """A device answered an RPC call with an error member."""

    def __init__(self, code: Any, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{message} (code: {code})")


def rpc_result(response: Any) -> Any:
    """The payload carried by a JSON-RPC response frame.

    A response that is not a frame is returned unchanged, so callers that
    already hold a bare payload keep working.

    Raises:
        RpcError: If the device answered with an error member.
    """
    if not isinstance(response, dict):
        return response

    error = response.get("error")
    if isinstance(error, dict):
        raise RpcError(error.get("code"), str(error.get("message", "Unknown error")))

    if "result" in response:
        return response["result"]
    return response
