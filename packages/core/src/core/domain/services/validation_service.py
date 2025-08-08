"""
Domain service for validation business logic.
"""


class ValidationService:

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        import ipaddress

        try:
            ipaddress.IPv4Address(ip)
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def validate_device_credentials(username: str | None, password: str | None) -> bool:
        if (username is None) != (password is None):
            return False

        if username and len(username) < 1:
            return False

        if password and len(password) < 1:
            return False

        return True

    @staticmethod
    def validate_scan_range(start_ip: str, end_ip: str) -> bool:
        import ipaddress

        try:
            start = ipaddress.IPv4Address(start_ip)
            end = ipaddress.IPv4Address(end_ip)
            return start <= end
        except ipaddress.AddressValueError:
            return False
