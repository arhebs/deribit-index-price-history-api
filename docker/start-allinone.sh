#!/usr/bin/env sh
set -eu

uv run alembic upgrade head
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
