"""
Tests for common utilities and decorators.
"""

import asyncio

import click
import pytest
from cli.commands.common import (
    async_command,
    create_scan_request,
    parse_ip_list,
)


class TestCommonUtilities:

    def test_parse_ip_list_with_valid_ips(self):
        ip_list_str = "192.168.1.100,192.168.1.101,192.168.1.102"
        result = parse_ip_list(ip_list_str)

        assert len(result) == 3
        assert "192.168.1.100" in result
        assert "192.168.1.101" in result
        assert "192.168.1.102" in result

    def test_parse_ip_list_with_spaces(self):
        ip_list_str = "192.168.1.100, 192.168.1.101 ,192.168.1.102"
        result = parse_ip_list(ip_list_str)

        assert len(result) == 3
        assert all(ip.strip() == ip for ip in result)

    def test_parse_ip_list_with_empty_string(self):
        result = parse_ip_list("")

        assert result == []

    def test_parse_ip_list_with_none(self):
        result = parse_ip_list(None)

        assert result == []

    def test_parse_ip_list_with_invalid_ip(self):
        ip_list_str = "192.168.1.100,invalid.ip.address,192.168.1.101"

        with pytest.raises(click.BadParameter):
            parse_ip_list(ip_list_str)

    # parse_ip_range was removed, tests moved to core/tests/unit/utils/test_target_parser.py

    # Removed validate_ip_address and validate_ip_range tests as they are no longer needed

    def test_create_scan_request_with_targets(self):
        scan_request = create_scan_request(
            targets=["192.168.1.0/24"],
            timeout=3.0,
            workers=10,
        )

        assert scan_request.targets == ["192.168.1.0/24"]
        assert scan_request.timeout == 3.0
        assert scan_request.max_workers == 10

    def test_create_scan_request_with_multiple_targets(self):
        scan_request = create_scan_request(
            targets=["192.168.1.100", "192.168.1.101"],
            timeout=5.0,
            workers=20,
        )

        assert scan_request.targets == ["192.168.1.100", "192.168.1.101"]
        assert scan_request.timeout == 5.0
        assert scan_request.max_workers == 20

    def test_create_scan_request_with_mdns(self):
        scan_request = create_scan_request(
            targets=[],
            use_mdns=True,
            timeout=3.0,
            workers=10,
        )

        assert scan_request.use_mdns is True
        assert scan_request.targets == []
        assert scan_request.timeout == 3.0
        assert scan_request.max_workers == 10

    def test_async_command_decorator(self):
        @async_command
        async def test_async_function():
            await asyncio.sleep(0.001)
            return "success"

        result = test_async_function()

        assert result == "success"

    def test_async_command_decorator_with_arguments(self):
        @async_command
        async def test_async_function_with_args(value):
            await asyncio.sleep(0.001)
            return f"result: {value}"

        result = test_async_function_with_args("test")

        assert result == "result: test"

    def test_async_command_decorator_handles_exceptions(self):
        @async_command
        async def test_async_function_with_exception():
            await asyncio.sleep(0.001)
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            test_async_function_with_exception()
