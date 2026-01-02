import pytest
from core.domain.value_objects.scan_request import ScanRequest
from pydantic import ValidationError


class TestScanRequest:

    def test_it_creates_scan_request_with_targets(self):
        request = ScanRequest(
            targets=["192.168.1.1", "192.168.1.10-20", "192.168.2.0/24"]
        )

        assert request.targets == ["192.168.1.1", "192.168.1.10-20", "192.168.2.0/24"]
        assert request.timeout == 3.0
        assert request.max_workers == 50

    def test_it_creates_scan_request_with_mdns(self):
        request = ScanRequest(use_mdns=True)
        assert request.use_mdns is True
        assert request.targets == []

    def test_it_fails_validation_if_no_targets_and_no_mdns(self):
        with pytest.raises(
            ValidationError,
            match="Either 'targets' must be provided or 'use_mdns' must be True",
        ):
            ScanRequest(use_mdns=False)

    def test_it_creates_scan_request_with_custom_timeout_and_workers(self):
        request = ScanRequest(
            targets=["192.168.1.1"],
            timeout=5.0,
            max_workers=100,
        )

        assert request.timeout == 5.0
        assert request.max_workers == 100

    def test_it_validates_valid_targets(self):
        valid_targets = [
            ["192.168.1.1"],
            ["192.168.1.1-10"],
            ["192.168.1.0/24"],
            ["192.168.1.1", "192.168.1.2"],
        ]

        for targets in valid_targets:
            request = ScanRequest(targets=targets)
            assert request.targets == targets

    def test_it_rejects_invalid_targets(self):
        invalid_targets = [
            ["256.1.1.1"],
            ["192.168.1"],
            ["192.168.1.1.1"],
            ["invalid.ip.address"],
            [""],
            ["192.168.1.1-"],
            ["192.168.1.0/33"],
        ]

        for targets in invalid_targets:
            with pytest.raises(ValidationError):
                ScanRequest(targets=targets)

    def test_it_validates_timeout_within_range(self):
        valid_timeouts = [0.1, 1.0, 5.0, 15.0, 30.0]

        for timeout in valid_timeouts:
            request = ScanRequest(use_mdns=True, timeout=timeout)
            assert request.timeout == timeout

    def test_it_rejects_timeout_below_minimum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_mdns=True, timeout=0.05)

    def test_it_rejects_timeout_above_maximum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_mdns=True, timeout=35.0)

    def test_it_validates_max_workers_within_range(self):
        valid_workers = [1, 10, 50, 100, 200]

        for workers in valid_workers:
            request = ScanRequest(use_mdns=True, max_workers=workers)
            assert request.max_workers == workers

    def test_it_rejects_max_workers_below_minimum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_mdns=True, max_workers=0)

    def test_it_rejects_max_workers_above_maximum(self):
        with pytest.raises(ValidationError):
            ScanRequest(use_mdns=True, max_workers=250)

    def test_it_validates_boundary_timeout_values(self):
        min_request = ScanRequest(use_mdns=True, timeout=0.1)
        max_request = ScanRequest(use_mdns=True, timeout=30.0)

        assert min_request.timeout == 0.1
        assert max_request.timeout == 30.0

    def test_it_validates_boundary_max_workers_values(self):
        min_request = ScanRequest(use_mdns=True, max_workers=1)
        max_request = ScanRequest(use_mdns=True, max_workers=200)

        assert min_request.max_workers == 1
        assert max_request.max_workers == 200
