import os
import asyncio
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from .base import Base


class DatabaseManager:
    """Manages database connections and sessions for Jarilo."""

    def __init__(self, database_url: str = "sqlite+aiosqlite:///" + os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "jarilo.db")):
        self.database_url = database_url
        self.engine = None
        self.async_session_maker = None

    async def init_db(self) -> None:
        """Initialize the database engine and create tables."""
        self.engine = create_async_engine(
            self.database_url,
            echo=False,  # Set to True for SQL logging during development
            poolclass=NullPool,  # Disable connection pooling for SQLite
        )

        self.async_session_maker = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def close_db(self) -> None:
        """Close the database engine."""
        if self.engine:
            await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async database session."""
        if not self.async_session_maker:
            raise RuntimeError("Database not initialized. Call init_db() first.")

        async with self.async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager instance
db_manager = DatabaseManager()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get database session."""
    async for session in db_manager.get_session():
        yield session