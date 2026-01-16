from __future__ import annotations

from decimal import Decimal

import pytest

from app.db.repository import PricePointRepository
from app.db.session import session_scope


@pytest.mark.integration
@pytest.mark.asyncio
async def test_upsert_overwrites_price_for_same_ticker_ts(
    test_database_url: str,
) -> None:
    async with session_scope(database_url=test_database_url) as session:
        repo = PricePointRepository(session)

        await repo.upsert_price_point(ticker="btc_usd", ts_unix=1, price=Decimal("1.1"))
        await session.commit()

        await repo.upsert_price_point(ticker="btc_usd", ts_unix=1, price=Decimal("2.2"))
        await session.commit()

        rows = await repo.list_range(
            ticker="btc_usd",
            from_ts=1,
            to_ts=1,
            limit=10,
            offset=0,
        )
        assert len(rows) == 1
        assert rows[0].ts_unix == 1
        assert rows[0].price == Decimal("2.2")
