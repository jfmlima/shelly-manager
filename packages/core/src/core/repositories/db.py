import os
from collections.abc import AsyncGenerator

from core.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
