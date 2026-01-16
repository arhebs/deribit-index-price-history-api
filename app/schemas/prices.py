from __future__ import annotations

from collections.abc import Sequence
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PricePointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    ts_unix: int
    price: Decimal


class PaginatedPricePointsOut(BaseModel):
    count: int
    next: str | None = Field(default=None)
    previous: str | None = Field(default=None)
    results: Sequence[PricePointOut]
