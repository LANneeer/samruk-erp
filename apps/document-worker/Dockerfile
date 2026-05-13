FROM python:3.12-slim AS builder

ENV POETRY_VERSION=2.1.1 \
  PIP_NO_CACHE_DIR=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential curl git \
  && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/poetry-venv \
  && /opt/poetry-venv/bin/pip install --upgrade pip \
  && /opt/poetry-venv/bin/pip install "poetry==${POETRY_VERSION}"
ENV PATH="/opt/poetry-venv/bin:$PATH"

WORKDIR /app

COPY packages ./packages

COPY apps/document-worker/pyproject.toml apps/document-worker/poetry.lock ./apps/document-worker/

WORKDIR /app/apps/document-worker

RUN POETRY_VIRTUALENVS_IN_PROJECT=true \
  poetry install --no-root --only main -n

COPY apps/document-worker/src ./src
COPY apps/document-worker/README.md ./README.md

FROM python:3.12-slim AS worker

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/packages ./packages
COPY --from=builder /app/apps/document-worker/pyproject.toml /app/apps/document-worker/poetry.lock ./apps/document-worker/

WORKDIR /app/apps/document-worker

COPY --from=builder /app/apps/document-worker/.venv ./.venv
COPY --from=builder /app/apps/document-worker/src ./src
COPY --from=builder /app/apps/document-worker/README.md ./README.md

ENV PATH="/app/apps/document-worker/.venv/bin:$PATH"

EXPOSE 8003
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
    CMD curl -fsS http://localhost:8003/docs >/dev/null || exit 1

CMD uvicorn src.cli.fastapi_app:app \
        --host 0.0.0.0 \
        --port 8003 \
        --reload \
        --reload-dir /app/apps/document-worker/src \
        --reload-dir /app/packages
