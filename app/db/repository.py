from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PricePoint


class PricePointRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_price_point(
        self, *, ticker: str, ts_unix: int, price: Decimal
    ) -> None:
        stmt = insert(PricePoint).values(ticker=ticker, ts_unix=ts_unix, price=price)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PricePoint.ticker, PricePoint.ts_unix],
            set_={"price": stmt.excluded.price},
        )
        await self._session.execute(stmt)

    async def count_price_points(
        self,
        *,
        ticker: str,
        from_ts: int | None = None,
        to_ts: int | None = None,
    ) -> int:
        stmt = (
            select(func.count())
            .select_from(PricePoint)
            .where(PricePoint.ticker == ticker)
        )
        if from_ts is not None:
            stmt = stmt.where(PricePoint.ts_unix >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(PricePoint.ts_unix <= to_ts)

        result = await self._session.execute(stmt)
        return int(result.scalar_one())

    async def list_price_points(
        self, *, ticker: str, limit: int, offset: int
    ) -> Sequence[PricePoint]:
        stmt = (
            select(PricePoint)
            .where(PricePoint.ticker == ticker)
            .order_by(PricePoint.ts_unix.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def get_latest(self, *, ticker: str) -> PricePoint | None:
        stmt = (
            select(PricePoint)
            .where(PricePoint.ticker == ticker)
            .order_by(PricePoint.ts_unix.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalars().first()

    async def list_range(
        self,
        *,
        ticker: str,
        from_ts: int | None,
        to_ts: int | None,
        limit: int,
        offset: int,
    ) -> Sequence[PricePoint]:
        stmt = select(PricePoint).where(PricePoint.ticker == ticker)
        if from_ts is not None:
            stmt = stmt.where(PricePoint.ts_unix >= from_ts)
        if to_ts is not None:
            stmt = stmt.where(PricePoint.ts_unix <= to_ts)

        stmt = stmt.order_by(PricePoint.ts_unix.asc()).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return result.scalars().all()
