from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection


async def try_advisory_lock(connection: AsyncConnection, *, key: int) -> bool:
    result = await connection.execute(
        text("SELECT pg_try_advisory_lock(:key)"), {"key": key}
    )
    return bool(result.scalar_one())


async def release_advisory_lock(connection: AsyncConnection, *, key: int) -> None:
    await connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": key})
