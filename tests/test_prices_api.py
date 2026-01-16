from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    def _override_db_session() -> Iterator[object]:
        yield object()

    app.dependency_overrides[get_db_session] = _override_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_prices_list_validates_ticker(client: TestClient) -> None:
    resp = client.get("/prices", params={"ticker": "nope"})
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "invalid_ticker"


def test_prices_latest_returns_404_when_empty(monkeypatch, client: TestClient) -> None:
    class _FakeService:
        async def latest_price(self, **_kwargs) -> None:
            return None

    monkeypatch.setattr("app.api.routes.prices.PriceService", _FakeService)

    resp = client.get("/prices/latest", params={"ticker": "btc_usd"})
    assert resp.status_code == 404
    assert resp.json()["detail"]["error"] == "not_found"


def test_prices_range_validates_range_order(client: TestClient) -> None:
    resp = client.get(
        "/prices/range",
        params={"ticker": "btc_usd", "from_ts": 10, "to_ts": 1},
    )
    assert resp.status_code == 422
    assert resp.json()["detail"]["error"] == "invalid_range"


def test_prices_list_and_range_envelope_shape(monkeypatch, client: TestClient) -> None:
    class _FakeService:
        async def count_prices(self, **_kwargs) -> int:
            return 2

        async def list_prices(self, **kwargs) -> list[object]:
            ticker = kwargs["ticker"]
            return [
                type(
                    "PP",
                    (),
                    {"ticker": ticker, "ts_unix": 1, "price": Decimal("1.1")},
                )(),
                type(
                    "PP",
                    (),
                    {"ticker": ticker, "ts_unix": 2, "price": Decimal("2.2")},
                )(),
            ]

        async def list_range(self, **kwargs) -> list[object]:
            return await self.list_prices(**kwargs)

        async def latest_price(self, **_kwargs) -> None:
            return None

    monkeypatch.setattr("app.api.routes.prices.PriceService", _FakeService)

    resp = client.get("/prices", params={"ticker": "btc_usd", "limit": 1, "offset": 0})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["count"] == 2
    assert payload["next"] is not None
    assert payload["previous"] is None
    assert len(payload["results"]) == 2
    assert payload["results"][0]["ticker"] == "btc_usd"

    resp2 = client.get(
        "/prices/range",
        params={"ticker": "btc_usd", "from_ts": 1, "to_ts": 2, "limit": 1, "offset": 0},
    )
    assert resp2.status_code == 200
    payload2 = resp2.json()
    assert payload2["count"] == 2
    assert payload2["results"][0]["ticker"] == "btc_usd"
