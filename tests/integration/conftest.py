from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session")
def test_database_url() -> str:
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to run integration tests")
    if url.startswith("sqlite"):
        pytest.skip("Integration tests require Postgres (asyncpg)")
    return url
