import os
from collections.abc import AsyncGenerator

from core.repositories.models import Base
from core.settings import settings
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Ensure the directory exists
db_path = settings.database_path()
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Database connection URL
# We use aiosqlite for async SQLite support
DB_URL = f"sqlite+aiosqlite:///{db_path}"

engine = create_async_engine(
    DB_URL,
    echo=False,  # Set to True for SQL query logging
    future=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def create_schema(target: AsyncEngine) -> None:
    async with target.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all adds new indexes only to tables it creates fresh, not to a
        # device_backups table that predates this index. Add it explicitly so
        # existing databases get it too.
        await conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_device_backups_created_at "
                "ON device_backups (created_at)"
            )
        )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
