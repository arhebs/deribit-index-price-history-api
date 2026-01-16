from __future__ import annotations

from app.api.pagination import build_paginated_response


class _FakeRequest:
    def __init__(self, url: str) -> None:
        self._url = url

    @property
    def url(self) -> str:
        return self._url


def test_build_paginated_response_next_previous() -> None:
    request = _FakeRequest("http://test/prices?ticker=btc_usd&limit=100&offset=0")

    payload = build_paginated_response(
        request,
        count=250,
        limit=100,
        offset=0,
        results=[{"x": 1}],
    )

    assert payload["next"] == "http://test/prices?limit=100&offset=100&ticker=btc_usd"
    assert payload["previous"] is None

    payload2 = build_paginated_response(
        request,
        count=250,
        limit=100,
        offset=100,
        results=[],
    )

    assert payload2["next"] == "http://test/prices?limit=100&offset=200&ticker=btc_usd"
    assert (
        payload2["previous"] == "http://test/prices?limit=100&offset=0&ticker=btc_usd"
    )


def test_build_paginated_response_preserves_extra_params() -> None:
    request = _FakeRequest(
        "http://test/prices/range?ticker=btc_usd&from_ts=1&to_ts=2&limit=10&offset=0"
    )

    payload = build_paginated_response(
        request,
        count=11,
        limit=10,
        offset=0,
        results=[],
    )

    assert (
        payload["next"]
        == "http://test/prices/range?from_ts=1&limit=10&offset=10&ticker=btc_usd&to_ts=2"
    )


def test_build_paginated_response_handles_no_query() -> None:
    request = _FakeRequest("http://test/prices")

    payload = build_paginated_response(
        request,
        count=0,
        limit=100,
        offset=0,
        results=[],
    )

    assert payload["next"] is None
    assert payload["previous"] is None
