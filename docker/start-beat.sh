#!/usr/bin/env sh
set -eu

uv run alembic upgrade head
exec uv run celery -A app.workers.celery_app.celery_app beat -l info
