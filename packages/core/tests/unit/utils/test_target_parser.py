"""
Tests for target parsing utilities.
"""

import pytest
from core.utils.target_parser import expand_targets, parse_target, validate_target


def test_it_parses_single_ip():
    result = list(parse_target("192.168.1.1"))
    assert result == ["192.168.1.1"]


def test_it_parses_ip_range_full():
    result = list(parse_target("192.168.1.1-192.168.1.3"))
    assert result == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]


def test_it_parses_ip_range_short():
    result = list(parse_target("192.168.1.1-3"))
    assert result == ["192.168.1.1", "192.168.1.2", "192.168.1.3"]


def test_it_parses_cidr():
    # /30 has 2 hosts
    result = list(parse_target("192.168.1.0/30"))
    assert result == ["192.168.1.1", "192.168.1.2"]


def test_it_parses_cidr_32():
    result = list(parse_target("192.168.1.1/32"))
    assert result == ["192.168.1.1"]


def test_it_expands_targets():
    targets = ["192.168.1.1", "192.168.1.10-12"]
    result = expand_targets(targets)
    assert result == ["192.168.1.1", "192.168.1.10", "192.168.1.11", "192.168.1.12"]


def test_it_validates_target_valid():
    validate_target("192.168.1.1")
    validate_target("192.168.1.1-50")
    validate_target("192.168.1.0/24")


def test_it_validates_target_invalid():
    with pytest.raises(ValueError):
        validate_target("invalid")
    with pytest.raises(ValueError):
        validate_target("192.168.1.256")
    with pytest.raises(ValueError):
        validate_target("192.168.1.0/33")
