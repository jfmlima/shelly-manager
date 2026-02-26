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
