"""
Dependency injection container for API layer.
"""

from core.dependencies.container_base import BaseContainer
from litestar.di import Provide


class APIContainer(BaseContainer):
    """Container for the API process."""


def get_dependencies(container: APIContainer) -> dict:
    return {
        "scan_interactor": Provide(
            lambda: container.get_scan_interactor(), sync_to_thread=False
        ),
        "execute_component_action_interactor": Provide(
            lambda: container.get_execute_component_action_interactor(),
            sync_to_thread=False,
        ),
        "component_actions_interactor": Provide(
            lambda: container.get_component_actions_interactor(),
            sync_to_thread=False,
        ),
        "status_interactor": Provide(
            lambda: container.get_status_interactor(), sync_to_thread=False
        ),
        "bulk_operations_use_case": Provide(
            lambda: container.get_bulk_operations_interactor(),
            sync_to_thread=False,
        ),
        "credentials_use_case": Provide(
            lambda: container.get_credentials_use_case(),
            sync_to_thread=False,
        ),
        "manage_profiles_use_case": Provide(
            lambda: container.get_manage_profiles_interactor(),
            sync_to_thread=False,
        ),
        "provision_device_use_case": Provide(
            lambda: container.get_provision_device_interactor(),
            sync_to_thread=False,
        ),
        "backup_use_case": Provide(
            lambda: container.get_backup_device_config_interactor(),
            sync_to_thread=False,
        ),
        "restore_use_case": Provide(
            lambda: container.get_restore_device_config_interactor(),
            sync_to_thread=False,
        ),
        "manage_schedules_use_case": Provide(
            lambda: container.get_manage_backup_schedules_interactor(),
            sync_to_thread=False,
        ),
        "run_due_backups_use_case": Provide(
            lambda: container.get_run_due_backups_interactor(),
            sync_to_thread=False,
        ),
        "update_device_from_local_interactor": Provide(
            lambda: container.get_update_device_from_local_interactor(),
            sync_to_thread=False,
        ),
        "local_firmware_releases_interactor": Provide(
            lambda: container.get_local_firmware_releases_interactor(),
            sync_to_thread=False,
        ),
        "manage_firmware_use_case": Provide(
            lambda: container.get_manage_firmware_interactor(),
            sync_to_thread=False,
        ),
    }
