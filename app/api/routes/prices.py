from __future__ import annotations

from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.pagination import build_paginated_response
from app.db.session import get_db_session
from app.schemas.prices import PaginatedPricePointsOut, PricePointOut
from app.services.price_service import SUPPORTED_TICKERS, PriceService

router = APIRouter(tags=["prices"])

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 1000


def _validate_ticker(ticker: str) -> str:
    if ticker not in SUPPORTED_TICKERS:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_ticker",
                "message": f"ticker must be one of {', '.join(SUPPORTED_TICKERS)}",
            },
        )
    return ticker


@router.get("/prices", response_model=PaginatedPricePointsOut)
async def list_prices(
    request: Request,
    ticker: str,
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    ticker = _validate_ticker(ticker)

    service = PriceService()
    count = await service.count_prices(session=session, ticker=ticker)
    results: Sequence[PricePointOut] = [
        PricePointOut.model_validate(p)
        for p in await service.list_prices(
            session=session, ticker=ticker, limit=limit, offset=offset
        )
    ]

    return build_paginated_response(
        request,
        count=count,
        limit=limit,
        offset=offset,
        results=results,
    )


@router.get("/prices/latest", response_model=PricePointOut)
async def latest_price(
    ticker: str,
    session: AsyncSession = Depends(get_db_session),
) -> PricePointOut:
    ticker = _validate_ticker(ticker)

    service = PriceService()
    price_point = await service.latest_price(session=session, ticker=ticker)
    if price_point is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "not_found",
                "message": "no price points for ticker",
            },
        )

    return PricePointOut.model_validate(price_point)


@router.get("/prices/range", response_model=PaginatedPricePointsOut)
async def list_prices_range(
    request: Request,
    ticker: str,
    from_ts: int | None = Query(default=None, ge=0),
    to_ts: int | None = Query(default=None, ge=0),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=_MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    ticker = _validate_ticker(ticker)

    if from_ts is not None and to_ts is not None and from_ts > to_ts:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_range",
                "message": "from_ts must be <= to_ts",
            },
        )

    service = PriceService()
    count = await service.count_prices(
        session=session,
        ticker=ticker,
        from_ts=from_ts,
        to_ts=to_ts,
    )

    results: Sequence[PricePointOut] = [
        PricePointOut.model_validate(p)
        for p in await service.list_range(
            session=session,
            ticker=ticker,
            from_ts=from_ts,
            to_ts=to_ts,
            limit=limit,
            offset=offset,
        )
    ]

    return build_paginated_response(
        request,
        count=count,
        limit=limit,
        offset=offset,
        results=results,
    )
