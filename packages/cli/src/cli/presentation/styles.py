"""
Standardized CLI colors and message formatting for consistent visualization.
"""

from core.domain.enums.enums import Status


class Colors:

    # Status colors
    SUCCESS = "green"
    WARNING = "yellow"
    ERROR = "red"
    INFO = "blue"
    MUTED = "dim"

    # Action colors
    PROCESS = "blue"
    CONFIG = "cyan"

    # Device status colors
    DEVICE_DETECTED = "green"
    DEVICE_UPDATE_AVAILABLE = "yellow"
    DEVICE_UPDATED = "blue"
    DEVICE_UNREACHABLE = "red"
    DEVICE_ERROR = "red"
    DEVICE_UNKNOWN = "white"


class Icons:

    # Status icons
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    INFO = "ℹ️"

    # Action icons
    SEARCH = "🔍"
    LIST = "📋"
    STATUS = "📊"
    REBOOT = "🔄"
    UPDATE = "⬆️"
    CONFIG = "⚙️"
    PACKAGE = "📦"
    ROCKET = "🚀"
    CELEBRATION = "🎉"
    SIGNAL = "📡"


class Messages:

    @staticmethod
    def success(message: str, icon: str = Icons.SUCCESS) -> str:
        return f"[{Colors.SUCCESS}]{icon} {message}[/{Colors.SUCCESS}]"

    @staticmethod
    def warning(message: str, icon: str = Icons.WARNING) -> str:
        return f"[{Colors.WARNING}]{icon} {message}[/{Colors.WARNING}]"

    @staticmethod
    def error(message: str, icon: str = Icons.ERROR) -> str:
        return f"[{Colors.ERROR}]{icon} {message}[/{Colors.ERROR}]"

    @staticmethod
    def info(message: str, icon: str = Icons.INFO) -> str:
        return f"[{Colors.INFO}]{icon} {message}[/{Colors.INFO}]"

    @staticmethod
    def process(message: str, icon: str = "") -> str:
        return f"[{Colors.PROCESS}]{icon + ' ' if icon else ''}{message}[/{Colors.PROCESS}]"

    @staticmethod
    def config(message: str, icon: str = Icons.CONFIG) -> str:
        return f"[{Colors.CONFIG}]{icon} {message}[/{Colors.CONFIG}]"

    @staticmethod
    def muted(message: str) -> str:
        return f"[{Colors.MUTED}]{message}[/{Colors.MUTED}]"

    @staticmethod
    def device_action(device_ip: str, action: str, icon: str = "") -> str:
        return f"[{Colors.PROCESS}]{icon + ' ' if icon else ''}{device_ip}: {action}[/{Colors.PROCESS}]"

    @staticmethod
    def device_success(device_ip: str, message: str) -> str:
        return f"[{Colors.SUCCESS}]{Icons.SUCCESS} {device_ip}: {message}[/{Colors.SUCCESS}]"

    @staticmethod
    def device_error(device_ip: str, error: str) -> str:
        return f"[{Colors.ERROR}]{Icons.ERROR} {device_ip}: {error}[/{Colors.ERROR}]"


def _status_key(status: str | Status) -> str:
    value = status.value if isinstance(status, Status) else str(status)
    return value.lower()


def get_device_status_style(status: str | Status) -> str:
    status_styles = {
        "detected": Colors.DEVICE_DETECTED,
        "updated": Colors.DEVICE_UPDATED,
        "update_available": Colors.DEVICE_UPDATE_AVAILABLE,
        "unreachable": Colors.DEVICE_UNREACHABLE,
        "error": Colors.DEVICE_ERROR,
    }
    return status_styles.get(_status_key(status), Colors.DEVICE_UNKNOWN)


_STATUS_LABELS = {
    "detected": "Detected",
    "updated": "Updated",
    "update_available": "Update Available",
    "no_update_needed": "Up to Date",
    "auth_required": "Auth Required",
    "not_shelly": "Not a Shelly Device",
    "unreachable": "Unreachable",
    "error": "Error",
}


def get_device_status_label(status: str | Status) -> str:
    key = _status_key(status)
    if key in _STATUS_LABELS:
        return _STATUS_LABELS[key]
    return key.replace("_", " ").title() if key else "Unknown"


def format_device_status(status: str | Status) -> str:
    style = get_device_status_style(status)
    label = get_device_status_label(status)
    return f"[{style}]{label}[/{style}]"
