from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Deribit Index Price History API")
app.include_router(health_router)
