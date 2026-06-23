from datetime import UTC, datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Credentials(Base):
    __tablename__ = "credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mac: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String, nullable=False, default="admin")
    password_ciphertext: Mapped[str] = mapped_column(String, nullable=False)
    last_seen_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(
        Integer, default=lambda: int(datetime.now(UTC).timestamp())
    )
    rotated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Credentials(mac='{self.mac}', username='{self.username}')>"


class ProvisioningProfiles(Base):
    __tablename__ = "provisioning_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    wifi_ssid: Mapped[str | None] = mapped_column(String, nullable=True)
    wifi_password_ciphertext: Mapped[str | None] = mapped_column(String, nullable=True)
    mqtt_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    mqtt_server: Mapped[str | None] = mapped_column(String, nullable=True)
    mqtt_user: Mapped[str | None] = mapped_column(String, nullable=True)
    mqtt_password_ciphertext: Mapped[str | None] = mapped_column(String, nullable=True)
    mqtt_topic_prefix_template: Mapped[str | None] = mapped_column(
        String, nullable=True
    )
    auth_password_ciphertext: Mapped[str | None] = mapped_column(String, nullable=True)
    device_name_template: Mapped[str | None] = mapped_column(String, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String, nullable=True)
    cloud_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[int] = mapped_column(
        Integer, default=lambda: int(datetime.now(UTC).timestamp())
    )
    updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ProvisioningProfiles(name='{self.name}', is_default={self.is_default})>"
        )


class DeviceBackups(Base):
    __tablename__ = "device_backups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_mac: Mapped[str] = mapped_column(String, nullable=False, index=True)
    device_ip: Mapped[str | None] = mapped_column(String, nullable=True)
    device_name: Mapped[str | None] = mapped_column(String, nullable=True)
    device_type: Mapped[str | None] = mapped_column(String, nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String, nullable=True)
    generation: Mapped[str] = mapped_column(String, nullable=False, default="gen2")
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String, nullable=False, default="manual")
    snapshot_ciphertext: Mapped[str] = mapped_column(String, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String, nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[int] = mapped_column(
        Integer, default=lambda: int(datetime.now(UTC).timestamp())
    )

    def __repr__(self) -> str:
        return (
            f"<DeviceBackups(id={self.id}, device_mac='{self.device_mac}', "
            f"source='{self.source}')>"
        )


class BackupSchedules(Base):
    __tablename__ = "backup_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    target_ips: Mapped[str] = mapped_column(String, nullable=False, default="[]")
    target_macs: Mapped[str] = mapped_column(String, nullable=False, default="[]")
    all_credentialed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    interval_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    retention_keep_last: Mapped[int | None] = mapped_column(Integer, nullable=True)
    retention_max_age_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_run_at: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_run_at: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    last_status: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[int] = mapped_column(
        Integer, default=lambda: int(datetime.now(UTC).timestamp())
    )
    updated_at: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<BackupSchedules(id={self.id}, name='{self.name}', "
            f"enabled={self.enabled})>"
        )
