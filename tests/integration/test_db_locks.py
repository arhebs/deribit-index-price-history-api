from __future__ import annotations

import pytest

from app.db.locks import release_advisory_lock, try_advisory_lock
from app.db.session import create_engine


@pytest.mark.integration
@pytest.mark.asyncio
async def test_try_advisory_lock_is_exclusive(test_database_url: str) -> None:
    engine = create_engine(database_url=test_database_url)

    async with engine.connect() as c1:
        async with engine.connect() as c2:
            locked1 = await try_advisory_lock(c1, key=12345)
            locked2 = await try_advisory_lock(c2, key=12345)

            assert locked1 is True
            assert locked2 is False

            await release_advisory_lock(c1, key=12345)

            locked3 = await try_advisory_lock(c2, key=12345)
            assert locked3 is True

    await engine.dispose()
