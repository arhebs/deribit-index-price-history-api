from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


def create_engine(*, database_url: str | None = None) -> AsyncEngine:
    settings = get_settings()
    url = database_url or settings.database_url
    return create_async_engine(url, pool_pre_ping=True)


def create_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    *, database_url: str | None = None
) -> AsyncIterator[AsyncSession]:
    engine = create_engine(database_url=database_url)
    session_factory = create_sessionmaker(engine)

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()


async def get_db_session() -> AsyncIterator[AsyncSession]:
    engine = create_engine()
    session_factory = create_sessionmaker(engine)

    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
            await engine.dispose()
