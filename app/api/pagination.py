from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class _RequestWithUrl(Protocol):
    @property
    def url(self) -> object: ...


def _replace_query_params(url: str, *, limit: int, offset: int) -> str:
    base, _, query = url.partition("?")
    params: dict[str, list[str]] = {}
    if query:
        for part in query.split("&"):
            if not part:
                continue
            key, _, value = part.partition("=")
            params.setdefault(key, []).append(value)

    params["limit"] = [str(limit)]
    params["offset"] = [str(offset)]

    encoded = "&".join(
        f"{k}={v}" for k in sorted(params.keys()) for v in params[k] if v is not None
    )
    return f"{base}?{encoded}" if encoded else base


def build_paginated_response(
    request: _RequestWithUrl,
    *,
    count: int,
    limit: int,
    offset: int,
    results: Sequence[object],
) -> dict[str, object]:
    url = str(request.url)

    next_url: str | None
    previous_url: str | None

    if offset + limit < count:
        next_url = _replace_query_params(url, limit=limit, offset=offset + limit)
    else:
        next_url = None

    if offset > 0:
        previous_url = _replace_query_params(
            url, limit=limit, offset=max(offset - limit, 0)
        )
    else:
        previous_url = None

    return {
        "count": count,
        "next": next_url,
        "previous": previous_url,
        "results": results,
    }
