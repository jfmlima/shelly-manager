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
    parse_ip_range,
    validate_ip_address,
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

    def test_parse_ip_range_with_dash_format(self):
        ip_range = "192.168.1.1-192.168.1.50"
        start, end = parse_ip_range(ip_range)

        assert start == "192.168.1.1"
        assert end == "192.168.1.50"

    def test_parse_ip_range_with_cidr_format(self):
        ip_range = "192.168.1.0/24"
        start, end = parse_ip_range(ip_range)

        assert start == "192.168.1.1"
        assert end == "192.168.1.254"

    def test_parse_ip_range_with_single_ip(self):
        ip_range = "192.168.1.100"
        start, end = parse_ip_range(ip_range)

        assert start == "192.168.1.100"
        assert end == "192.168.1.100"

    def test_parse_ip_range_with_invalid_dash_format(self):
        ip_range = "192.168.1.1-192.168.1.50-192.168.1.100"

        with pytest.raises(ValueError):
            parse_ip_range(ip_range)

    def test_parse_ip_range_with_invalid_cidr(self):
        ip_range = "192.168.1.0/33"

        with pytest.raises(ValueError):
            parse_ip_range(ip_range)

    def test_validate_ip_address_with_valid_ip(self):
        ctx = None
        param = None
        value = "192.168.1.100"

        result = validate_ip_address(ctx, param, value)

        assert result == value

    def test_validate_ip_address_with_multiple_valid_ips(self):
        ctx = None
        param = None
        value = ("192.168.1.100", "192.168.1.101")

        result = validate_ip_address(ctx, param, value)

        assert result == value

    def test_validate_ip_address_with_invalid_ip(self):
        ctx = None
        param = None
        value = "invalid.ip.address"

        with pytest.raises(click.BadParameter):
            validate_ip_address(ctx, param, value)

    def test_create_scan_request_with_ip_ranges(self):
        scan_request = create_scan_request(
            ip_ranges=["192.168.1.0/24"],
            devices=[],
            from_config=False,
            timeout=3.0,
            workers=10,
        )

        assert scan_request.start_ip is not None
        assert scan_request.use_predefined is False
        assert scan_request.timeout == 3.0
        assert scan_request.max_workers == 10

    def test_create_scan_request_with_specific_devices(self):
        scan_request = create_scan_request(
            ip_ranges=[],
            devices=["192.168.1.100", "192.168.1.101"],
            from_config=False,
            timeout=5.0,
            workers=20,
        )

        assert scan_request.use_predefined is False
        assert scan_request.timeout == 5.0
        assert scan_request.max_workers == 20

    def test_create_scan_request_from_config(self):
        scan_request = create_scan_request(
            ip_ranges=[],
            devices=[],
            from_config=True,
            timeout=3.0,
            workers=10,
        )

        assert scan_request.use_predefined is True
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
