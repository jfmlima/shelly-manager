import pytest
from core.gateways.network.rpc_envelope import RpcError, rpc_result

# Frames captured verbatim from a Shelly Gen4 (S4SW-001P8EU, fw 1.7.1) over
# POST /rpc. Both arrive as HTTP 200; only the member distinguishes them.
SUCCESS_FRAME = {
    "id": "probe-1",
    "src": "shelly1pmminig4-7c2c676d30d4",
    "result": {"id": 0, "name": None, "in_mode": "flip", "auto_off_delay": 60.0},
}
ERROR_FRAME = {
    "id": "probe-4",
    "src": "shelly1pmminig4-7c2c676d30d4",
    "error": {"code": -105, "message": "Argument 'id', value 99 not found!"},
}


class TestRpcResult:
    def test_it_returns_the_payload_not_the_frame(self):
        assert rpc_result(SUCCESS_FRAME) == {
            "id": 0,
            "name": None,
            "in_mode": "flip",
            "auto_off_delay": 60.0,
        }

    def test_it_raises_on_a_device_rejection(self):
        with pytest.raises(RpcError) as excinfo:
            rpc_result(ERROR_FRAME)

        assert excinfo.value.code == -105
        assert "value 99 not found" in str(excinfo.value)

    def test_it_returns_an_empty_result_as_is(self):
        # A method with no return value answers with an empty result member.
        assert rpc_result({"id": "x", "src": "y", "result": {}}) == {}

    def test_it_passes_through_a_response_that_is_not_a_frame(self):
        assert rpc_result({"methods": ["Switch.Toggle"]}) == {
            "methods": ["Switch.Toggle"]
        }

    def test_it_passes_through_a_non_mapping(self):
        assert rpc_result(None) is None
