"""Async SQLAlchemy session factory and engine configuration."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

try:
    from sqlalchemy.ext.asyncio import (
        AsyncEngine,
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )
    from sqlalchemy.pool import NullPool

    def build_async_engine(database_url: str, echo: bool = False) -> AsyncEngine:
        """Creates a configured async SQLAlchemy engine.

        Args:
            database_url: PostgreSQL async DSN (postgresql+asyncpg://...).
            echo: If True, emits SQL statements to stdout for debugging.

        Returns:
            Configured AsyncEngine instance.
        """
        return create_async_engine(
            database_url,
            echo=echo,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )

    def build_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        """Creates a reusable async session factory bound to given engine.

        Args:
            engine: Initialized AsyncEngine.

        Returns:
            async_sessionmaker instance for creating AsyncSession objects.
        """
        return async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def get_db_session(
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[AsyncSession, None]:
        """Context manager providing a transactional database session.

        Yields:
            AsyncSession with automatic rollback on exception.
        """
        async with session_factory() as session:
            async with session.begin():
                try:
                    yield session
                except Exception:
                    await session.rollback()
                    raise

except ImportError:
    # Graceful fallback for environments without SQLAlchemy
    def build_async_engine(*args, **kwargs):  # type: ignore
        return None

    def build_session_factory(*args, **kwargs):  # type: ignore
        return None

    def get_db_session(*args, **kwargs):  # type: ignore
        raise ImportError("sqlalchemy[asyncio] is required for database sessions.")
