import pytest
from core.domain.value_objects.scan_request import ScanRequest
from pydantic import ValidationError


class TestScanRequest:

    def test_it_creates_scan_request_with_ip_range(self):
        request = ScanRequest(
            start_ip="192.168.1.1", end_ip="192.168.1.10", use_predefined=False
        )

        assert request.start_ip == "192.168.1.1"
        assert request.end_ip == "192.168.1.10"
        assert request.use_predefined is False
        assert request.timeout == 3.0
        assert request.max_workers == 50

    def test_it_creates_scan_request_with_predefined_ips(self):
        request = ScanRequest(use_predefined=True)

        assert request.start_ip is None
        assert request.end_ip is None
        assert request.use_predefined is True
        assert request.timeout == 3.0
        assert request.max_workers == 50

    def test_it_creates_scan_request_with_custom_timeout_and_workers(self):
        request = ScanRequest(
            start_ip="192.168.1.1",
            end_ip="192.168.1.5",
            use_predefined=False,
            timeout=5.0,
            max_workers=100,
        )

        assert request.timeout == 5.0
        assert request.max_workers == 100

    def test_it_validates_valid_ip_addresses(self):
        valid_ips = [
            ("192.168.1.1", "192.168.1.10"),
            ("10.0.0.1", "10.0.0.255"),
            ("172.16.0.1", "172.16.255.255"),
            ("0.0.0.0", "255.255.255.255"),
        ]

        for start_ip, end_ip in valid_ips:
            request = ScanRequest(
                start_ip=start_ip, end_ip=end_ip, use_predefined=False
            )
            assert request.start_ip == start_ip
            assert request.end_ip == end_ip

    def test_it_rejects_invalid_start_ip_addresses(self):
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "invalid.ip.address",
            "",
            "192.168.1.-1",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValidationError):
                ScanRequest(start_ip=ip, end_ip="192.168.1.10", use_predefined=False)

    def test_it_rejects_invalid_end_ip_addresses(self):
        invalid_ips = [
            "256.1.1.1",
            "192.168.1",
            "192.168.1.1.1",
            "invalid.ip.address",
            "",
            "192.168.1.-1",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValidationError):
                ScanRequest(start_ip="192.168.1.1", end_ip=ip, use_predefined=False)

    def test_it_validates_ip_range_order(self):
        request = ScanRequest(
            start_ip="192.168.1.1", end_ip="192.168.1.10", use_predefined=False
        )

        assert request.start_ip == "192.168.1.1"
        assert request.end_ip == "192.168.1.10"

    def test_it_validates_same_start_and_end_ip(self):
        request = ScanRequest(
            start_ip="192.168.1.100", end_ip="192.168.1.100", use_predefined=False
        )

        assert request.start_ip == "192.168.1.100"
        assert request.end_ip == "192.168.1.100"

    def test_it_rejects_start_ip_greater_than_end_ip(self):
        with pytest.raises(
            ValidationError, match="start_ip must be less than or equal to end_ip"
        ):
            ScanRequest(
                start_ip="192.168.1.10", end_ip="192.168.1.1", use_predefined=False
            )

    def test_it_validates_timeout_within_range(self):
        valid_timeouts = [0.1, 1.0, 5.0, 15.0, 30.0]

        for timeout in valid_timeouts:
            request = ScanRequest(use_predefined=True, timeout=timeout)
            assert request.timeout == timeout

    def test_it_rejects_timeout_below_minimum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_predefined=True, timeout=0.05)

    def test_it_rejects_timeout_above_maximum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_predefined=True, timeout=35.0)

    def test_it_validates_max_workers_within_range(self):
        valid_workers = [1, 10, 50, 100, 200]

        for workers in valid_workers:
            request = ScanRequest(use_predefined=True, max_workers=workers)
            assert request.max_workers == workers

    def test_it_rejects_max_workers_below_minimum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_predefined=True, max_workers=0)

    def test_it_rejects_max_workers_above_maximum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_predefined=True, max_workers=250)

    def test_it_allows_none_ip_addresses_when_using_predefined(self):
        request = ScanRequest(start_ip=None, end_ip=None, use_predefined=True)

        assert request.start_ip is None
        assert request.end_ip is None
        assert request.use_predefined is True

    def test_it_validates_cross_subnet_ip_range(self):
        request = ScanRequest(
            start_ip="192.168.1.255", end_ip="192.168.2.1", use_predefined=False
        )

        assert request.start_ip == "192.168.1.255"
        assert request.end_ip == "192.168.2.1"

    def test_it_validates_large_ip_range(self):
        request = ScanRequest(
            start_ip="10.0.0.1", end_ip="10.255.255.255", use_predefined=False
        )

        assert request.start_ip == "10.0.0.1"
        assert request.end_ip == "10.255.255.255"

    def test_it_defaults_use_predefined_to_true(self):
        request = ScanRequest()

        assert request.use_predefined is True
        assert request.timeout == 3.0
        assert request.max_workers == 50

    def test_it_validates_boundary_timeout_values(self):
        min_request = ScanRequest(use_predefined=True, timeout=0.1)
        max_request = ScanRequest(use_predefined=True, timeout=30.0)

        assert min_request.timeout == 0.1
        assert max_request.timeout == 30.0

    def test_it_validates_boundary_max_workers_values(self):
        min_request = ScanRequest(use_predefined=True, max_workers=1)
        max_request = ScanRequest(use_predefined=True, max_workers=200)

        assert min_request.max_workers == 1
        assert max_request.max_workers == 200

    def test_it_handles_only_start_ip_specified(self):
        request = ScanRequest(start_ip="192.168.1.1", end_ip=None, use_predefined=False)

        assert request.start_ip == "192.168.1.1"
        assert request.end_ip is None

    def test_it_handles_only_end_ip_specified(self):
        request = ScanRequest(
            start_ip=None, end_ip="192.168.1.10", use_predefined=False
        )

        assert request.start_ip is None
        assert request.end_ip == "192.168.1.10"

    def test_it_validates_range_with_start_ip_but_no_end_ip(self):
        request = ScanRequest(start_ip="192.168.1.1", end_ip=None, use_predefined=False)

        assert request.start_ip == "192.168.1.1"
        assert request.end_ip is None

    def test_it_creates_minimal_scan_request(self):
        request = ScanRequest(use_predefined=False)

        assert request.start_ip is None
        assert request.end_ip is None
        assert request.use_predefined is False
        assert request.timeout == 3.0
        assert request.max_workers == 50
