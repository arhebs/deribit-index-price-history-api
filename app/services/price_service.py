from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.locks import release_advisory_lock, try_advisory_lock
from app.db.models import PricePoint
from app.db.repository import PricePointRepository
from app.db.session import create_engine, create_sessionmaker
from app.deribit.client import DeribitClient

SUPPORTED_TICKERS: tuple[str, ...] = ("btc_usd", "eth_usd")


def compute_minute_bucket(now_ts: int | None = None) -> int:
    ts = int(now_ts if now_ts is not None else time.time())
    return (ts // 60) * 60


@dataclass(frozen=True)
class IngestResult:
    ts_unix: int
    tickers: Sequence[str]


class PriceService:
    _ingest_lock_key: int = 640_001

    async def poll_and_store_prices(self) -> IngestResult | None:
        ts_unix = compute_minute_bucket()

        engine = create_engine()
        session_factory = create_sessionmaker(engine)

        async with engine.connect() as connection:
            locked = await try_advisory_lock(connection, key=self._ingest_lock_key)
            if not locked:
                await engine.dispose()
                return None

            try:
                async with session_factory(bind=connection) as session:
                    repo = PricePointRepository(session)

                    async with DeribitClient() as deribit:
                        for ticker in SUPPORTED_TICKERS:
                            price = await deribit.get_index_price(ticker)
                            await repo.upsert_price_point(
                                ticker=ticker, ts_unix=ts_unix, price=price
                            )

                    await session.commit()
            finally:
                await release_advisory_lock(connection, key=self._ingest_lock_key)
                await engine.dispose()

        return IngestResult(ts_unix=ts_unix, tickers=SUPPORTED_TICKERS)

    async def list_prices(
        self, *, session: AsyncSession, ticker: str, limit: int, offset: int
    ) -> Sequence[PricePoint]:
        return await PricePointRepository(session).list_price_points(
            ticker=ticker, limit=limit, offset=offset
        )

    async def count_prices(
        self,
        *,
        session: AsyncSession,
        ticker: str,
        from_ts: int | None = None,
        to_ts: int | None = None,
    ) -> int:
        return await PricePointRepository(session).count_price_points(
            ticker=ticker, from_ts=from_ts, to_ts=to_ts
        )

    async def latest_price(
        self, *, session: AsyncSession, ticker: str
    ) -> PricePoint | None:
        return await PricePointRepository(session).get_latest(ticker=ticker)

    async def list_range(
        self,
        *,
        session: AsyncSession,
        ticker: str,
        from_ts: int | None,
        to_ts: int | None,
        limit: int,
        offset: int,
    ) -> Sequence[PricePoint]:
        return await PricePointRepository(session).list_range(
            ticker=ticker,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
            offset=offset,
        )
