from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PricePoint(Base):
    __tablename__ = "price_points"
    __table_args__ = (
        UniqueConstraint("ticker", "ts_unix", name="uq_price_points_ticker_ts_unix"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String, nullable=False)
    ts_unix: Mapped[int] = mapped_column(BigInteger, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


Index("ix_price_points_ticker_ts_unix", PricePoint.ticker, PricePoint.ts_unix)
Index("ix_price_points_ts_unix", PricePoint.ts_unix)
