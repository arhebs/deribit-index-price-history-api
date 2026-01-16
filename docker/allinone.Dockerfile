FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl supervisor redis-server \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini

COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY docker/start-allinone.sh ./docker/start-allinone.sh
COPY docker/start-api.sh ./docker/start-api.sh
COPY docker/start-worker.sh ./docker/start-worker.sh
COPY docker/start-beat.sh ./docker/start-beat.sh

EXPOSE 8000

CMD ["./docker/start-allinone.sh"]
