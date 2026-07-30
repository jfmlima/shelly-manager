"""Exit codes and typed error mapping for CLI commands."""

from core.domain.entities.exceptions import (
    DeviceAuthenticationError,
    DeviceCommunicationError,
    DeviceNotFoundError,
)
from core.use_cases.backup_device_config import BackupError, BackupNotFoundError
from core.use_cases.manage_backup_schedules import (
    ScheduleAlreadyExistsError,
    ScheduleNotFoundError,
)
from core.use_cases.manage_credentials import CredentialNotFoundError
from core.use_cases.manage_provisioning_profiles import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from core.use_cases.restore_device_config import DeviceMismatchError

EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_NOT_FOUND = 3
EXIT_AUTH = 4
EXIT_COMMUNICATION = 5
EXIT_CONFLICT = 6
EXIT_VALIDATION = 7

NOT_FOUND_ERRORS = (
    DeviceNotFoundError,
    BackupNotFoundError,
    CredentialNotFoundError,
    ProfileNotFoundError,
    ScheduleNotFoundError,
)
CONFLICT_ERRORS = (
    DeviceMismatchError,
    ProfileAlreadyExistsError,
    ScheduleAlreadyExistsError,
)


class OperationCancelledError(Exception):
    """Raised when the user declines a confirmation prompt."""


def exit_code_for(error: BaseException) -> int:
    if isinstance(error, NOT_FOUND_ERRORS):
        return EXIT_NOT_FOUND
    if isinstance(error, DeviceAuthenticationError):
        return EXIT_AUTH
    if isinstance(error, DeviceCommunicationError):
        return EXIT_COMMUNICATION
    if isinstance(error, CONFLICT_ERRORS):
        return EXIT_CONFLICT
    if isinstance(error, BackupError | ValueError):
        return EXIT_VALIDATION
    return EXIT_ERROR
