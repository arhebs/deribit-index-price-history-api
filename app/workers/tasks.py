from __future__ import annotations

from app.core.logging import configure_logging
from app.services.price_service import PriceService
from app.workers.celery_app import celery_app
from app.workers.runtime import run_async

configure_logging()


@celery_app.task(name="poll_deribit_index_prices")
def poll_deribit_index_prices() -> dict[str, object]:
    service = PriceService()
    result = run_async(service.poll_and_store_prices())

    if result is None:
        return {"skipped": True}

    return {
        "skipped": False,
        "ts_unix": result.ts_unix,
        "tickers": list(result.tickers),
    }
