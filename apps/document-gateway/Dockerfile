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

COPY apps/document-gateway/pyproject.toml apps/document-gateway/poetry.lock ./apps/document-gateway/

WORKDIR /app/apps/document-gateway

RUN POETRY_VIRTUALENVS_IN_PROJECT=true \
  poetry install --no-root --only main -n

COPY apps/document-gateway/src ./src
COPY apps/document-gateway/README.md ./README.md

#############################################################################
#                             Stage 2: run app                              #
#############################################################################
FROM python:3.12-slim AS api

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/packages ./packages
COPY --from=builder /app/apps/document-gateway/pyproject.toml /app/apps/document-gateway/poetry.lock ./apps/document-gateway/

WORKDIR /app/apps/document-gateway

COPY --from=builder /app/apps/document-gateway/.venv ./.venv
COPY --from=builder /app/apps/document-gateway/src ./src
COPY --from=builder /app/apps/document-gateway/README.md ./README.md

ENV PATH="/app/apps/document-gateway/.venv/bin:$PATH"

EXPOSE 8002
HEALTHCHECK --interval=60s --timeout=3s --retries=3 \
    CMD curl -fsS http://localhost:8002/docs >/dev/null || exit 1

# without [] and "exec" the container stop will be stopping for 10 seconds
CMD [ "/bin/sh" , "-c", "\
    exec uvicorn src.fastapi_app:app \
        --host 0.0.0.0 \
        --port 8002 \
        --reload \
        --reload-dir /app/apps/document-gateway/src \
        --reload-dir /app/packages \
"]
