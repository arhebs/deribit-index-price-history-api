# Deribit Index Price Collector + Price History API

Backend service that polls Deribit index prices for `btc_usd` and `eth_usd` once per minute, stores them in PostgreSQL,
and exposes a FastAPI API for querying historical time-series.

Stack: FastAPI + Celery (worker + beat) + PostgreSQL + Redis.

## How to Run

Prereqs: Docker + Docker Compose.

```bash
# Fresh start (optional)
docker compose down -v --remove-orphans

# Start stack (Postgres + Redis + migrate + api + worker + beat)
docker compose up --build
```

Note: this compose file maps Postgres/Redis to non-default host ports
(15432 and 16379) to avoid conflicts with existing local services.

## Quick Start (Docker)

API is exposed at `http://127.0.0.1:8000`.

- Health: `GET /health`
- OpenAPI: `http://127.0.0.1:8000/docs`

## Local Development (uv)

Prereqs: Python 3.12 and `uv`.

```bash
uv sync --group dev

# Apply migrations
uv run alembic upgrade head

# Run API
uv run uvicorn app.main:app --reload

# Run Celery worker (separate terminal)
uv run celery -A app.workers.celery_app.celery_app worker -l info

# Run Celery beat (separate terminal)
uv run celery -A app.workers.celery_app.celery_app beat -l info
```

## Configuration

The service uses `.env` (gitignored). Copy `.env.example`:

```bash
cp .env.example .env
```

Required environment variables:

- `DATABASE_URL` (SQLAlchemy async URL, `postgresql+asyncpg://...`)
- `REDIS_URL` (Celery broker)

Optional:

- `DERIBIT_BASE_URL` (defaults to testnet `https://test.deribit.com/api/v2`)
- `LOG_LEVEL` (defaults to `INFO`)

## API

All endpoints require a `ticker` query param and only accept `btc_usd` or `eth_usd`.

### List prices

```bash
curl "http://127.0.0.1:8000/prices?ticker=btc_usd&limit=100&offset=0"
```

### Latest price

```bash
curl "http://127.0.0.1:8000/prices/latest?ticker=btc_usd"
```

### Range query

```bash
curl "http://127.0.0.1:8000/prices/range?ticker=btc_usd&from_ts=1700000000&to_ts=1700003600&limit=100&offset=0"
```

## Testing

```bash
uv run pytest
uv run basedpyright
uv run ruff check .
uv run ruff format --check .
```

Integration tests require Postgres and are skipped unless `TEST_DATABASE_URL` is set.

Run them explicitly:

```bash
# Start stack (or bring your own Postgres)
docker compose up -d postgres

export TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/deribit"

uv run pytest -m integration -q
```

## Sanity Run Transcript (optional)

```bash
# Start stack
$ docker compose up --build -d

# Health
$ curl -sS http://127.0.0.1:8000/health
{"status":"ok"}

# After ~1 minute
$ curl -sS "http://127.0.0.1:8000/prices/latest?ticker=btc_usd"
{"ticker":"btc_usd","ts_unix":<minute_bucket>,"price":"..."}
```

## Design Decisions

- **Minute bucket timestamps**: samples are stored at `ts_unix = floor(now / 60) * 60` to produce one stable bucket per
  minute, making ingestion idempotent (retries land in the same bucket) and simplifying time-series queries.
- **Why advisory locks (in addition to unique constraints)**: `UNIQUE (ticker, ts_unix)` + UPSERT guarantees data
  integrity, but it doesn’t prevent wasted work if multiple workers overlap (duplicate Deribit calls + duplicate DB
  writes). A Postgres advisory lock makes the ingest job single-flight across workers/retries.
- **Price precision (Decimal → Numeric)**: Deribit JSON values are parsed into `Decimal` (via `Decimal(str(x))`), stored
  in Postgres as `NUMERIC(20, 10)`, and returned as a JSON string to avoid IEEE-754 float rounding.
- **Startup race handling**: `docker-compose.yml` uses a `pg_isready` healthcheck for Postgres plus a one-shot `migrate`
  service. `api/worker/beat` depend on migrations completing successfully before starting.
- **Pagination envelope**: list endpoints return `{count, next, previous, results}` with `limit`/`offset`. Pagination
  links preserve original query params and only rewrite `limit`/`offset`.
- **Deribit error semantics**: Deribit can return HTTP 200 with a JSON-RPC `error` payload; the client treats that as a
  failure and raises typed exceptions (rate limit vs generic RPC error).

## Docker Notes

### Default (5 services)

`docker-compose.yml` includes:

- `postgres` with a `pg_isready` healthcheck
- a one-shot `migrate` service (Alembic)
- `depends_on` conditions so `api/worker/beat` wait for Postgres readiness and successful migrations

All application services build from the same Dockerfile (`docker/allinone.Dockerfile`) and differ only by the
container command (API vs worker vs beat vs migrations).

### Two-container option (app + Postgres)

This is an optional setup that runs API + Celery worker + Celery beat + Redis (broker) inside a single container.

```bash
docker compose -f docker-compose.two.yml up --build
```

