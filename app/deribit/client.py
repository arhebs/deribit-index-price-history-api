from __future__ import annotations

from decimal import Decimal

import aiohttp

from app.core.config import get_settings
from app.deribit.errors import DeribitHttpError, DeribitRateLimitError, DeribitRpcError


class DeribitClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        timeout_seconds: float = 10.0,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        settings = get_settings()
        self._base_url = (base_url or settings.deribit_base_url).rstrip("/")
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session = session
        self._owned_session: aiohttp.ClientSession | None = None

    async def get_index_price(self, index_name: str) -> Decimal:
        url = f"{self._base_url}/public/get_index_price"

        try:
            session = self._get_session()
            async with session.get(url, params={"index_name": index_name}) as resp:
                body_text = await resp.text()
                if resp.status != 200:
                    raise DeribitHttpError(status=resp.status, body=body_text)
                payload = await resp.json()
        except aiohttp.ClientError as exc:
            raise DeribitHttpError(status=0, body=str(exc)) from exc

        if isinstance(payload, dict) and payload.get("error"):
            error = payload["error"]
            code = int(error.get("code"))
            message = str(error.get("message"))
            data = error.get("data")

            if code in {10028, 10029}:
                raise DeribitRateLimitError(code=code, message=message, data=data)
            raise DeribitRpcError(code=code, message=message, data=data)

        try:
            result = payload["result"]
            index_price = result["index_price"]
        except (KeyError, TypeError) as exc:
            raise DeribitRpcError(
                code=-1, message="unexpected response shape", data=payload
            ) from exc

        return Decimal(str(index_price))

    async def close(self) -> None:
        if self._owned_session is None:
            return
        await self._owned_session.close()
        self._owned_session = None

    def _get_session(self) -> aiohttp.ClientSession:
        if self._session is not None:
            return self._session
        if self._owned_session is None:
            self._owned_session = aiohttp.ClientSession(timeout=self._timeout)
        return self._owned_session
