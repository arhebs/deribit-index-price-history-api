from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings


@pytest.fixture(autouse=True, scope="session")
def _set_required_env_vars() -> None:
    os.environ.setdefault(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
    )
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    get_settings.cache_clear()
