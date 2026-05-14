#############################################################################
#                           Stage 1: build wheels                           #
#############################################################################
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
COPY apps/document-worker/alembic ./alembic
COPY apps/document-worker/alembic.ini ./alembic.ini
COPY apps/document-worker/README.md ./README.md

#############################################################################
#                             Stage 2: run app                              #
#############################################################################
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
COPY --from=builder /app/apps/document-worker/alembic ./alembic
COPY --from=builder /app/apps/document-worker/alembic.ini ./alembic.ini
COPY --from=builder /app/apps/document-worker/README.md ./README.md

ENV PATH="/app/apps/document-worker/.venv/bin:$PATH"

EXPOSE 8003
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
    CMD curl -fsS http://localhost:8003/docs >/dev/null || exit 1

# without [] and "exec" the container stop will be stopping for 10 seconds
CMD [ "/bin/sh" , "-c", "\
    alembic upgrade head && \
    exec watchmedo auto-restart \
        --patterns='*.py' \
        --recursive \
        --directory=/app/apps/document-worker/src \
        --directory=/app/packages \
        -- celery -A src.celery_app:celery_app worker --loglevel=info \
"]
