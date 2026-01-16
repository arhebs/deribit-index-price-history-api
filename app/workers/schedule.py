from __future__ import annotations

from celery.schedules import crontab


beat_schedule = {
    "poll-deribit-index-prices-every-minute": {
        "task": "poll_deribit_index_prices",
        "schedule": crontab(minute="*"),
    }
}
