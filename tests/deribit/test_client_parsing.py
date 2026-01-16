from __future__ import annotations

from decimal import Decimal

import pytest
from aioresponses import aioresponses

from app.deribit.client import DeribitClient
from app.deribit.errors import DeribitRateLimitError, DeribitRpcError


@pytest.mark.asyncio
async def test_get_index_price_parses_decimal() -> None:
    client = DeribitClient(base_url="https://test.deribit.com/api/v2")

    with aioresponses() as mocked:
        mocked.get(
            "https://test.deribit.com/api/v2/public/get_index_price?index_name=btc_usd",
            payload={
                "jsonrpc": "2.0",
                "result": {
                    "index_price": 11628.81,
                    "estimated_delivery_price": 11628.81,
                },
                "id": 123,
            },
        )

        try:
            price = await client.get_index_price("btc_usd")
        finally:
            await client.close()

    assert price == Decimal("11628.81")


@pytest.mark.asyncio
async def test_get_index_price_rate_limit_errors() -> None:
    client = DeribitClient(base_url="https://test.deribit.com/api/v2")

    with aioresponses() as mocked:
        mocked.get(
            "https://test.deribit.com/api/v2/public/get_index_price?index_name=btc_usd",
            payload={
                "jsonrpc": "2.0",
                "error": {"code": 10029, "message": "rate_limit", "data": {}},
                "id": 123,
            },
        )

        try:
            with pytest.raises(DeribitRateLimitError) as excinfo:
                await client.get_index_price("btc_usd")
        finally:
            await client.close()

    assert excinfo.value.code == 10029
    assert excinfo.value.message == "rate_limit"


@pytest.mark.asyncio
async def test_get_index_price_other_rpc_error() -> None:
    client = DeribitClient(base_url="https://test.deribit.com/api/v2")

    with aioresponses() as mocked:
        mocked.get(
            "https://test.deribit.com/api/v2/public/get_index_price?index_name=btc_usd",
            payload={
                "jsonrpc": "2.0",
                "error": {"code": 10009, "message": "invalid_argument", "data": {}},
                "id": 123,
            },
        )

        try:
            with pytest.raises(DeribitRpcError) as excinfo:
                await client.get_index_price("btc_usd")
        finally:
            await client.close()

    assert excinfo.value.code == 10009
    assert excinfo.value.message == "invalid_argument"
