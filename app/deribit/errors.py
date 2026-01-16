from __future__ import annotations


class DeribitError(Exception):
    pass


class DeribitHttpError(DeribitError):
    def __init__(self, *, status: int, body: str | None = None) -> None:
        super().__init__(f"Deribit HTTP error {status}")
        self.status = status
        self.body = body


class DeribitRpcError(DeribitError):
    def __init__(self, *, code: int, message: str, data: object | None = None) -> None:
        super().__init__(f"Deribit RPC error {code}: {message}")
        self.code = code
        self.message = message
        self.data = data


class DeribitRateLimitError(DeribitRpcError):
    pass
