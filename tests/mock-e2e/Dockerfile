FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY tests/mock-e2e ./tests/mock-e2e

# without [] and "exec" the container stop will be stopping for 10 seconds
CMD ["sh", "-c", "\
    sleep 15 && \
    exec python tests/mock-e2e/fill_grafana_dashboards.py \
"]
