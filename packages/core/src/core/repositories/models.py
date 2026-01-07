from datetime import UTC, datetime

from sqlalchemy import Integer, String
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
