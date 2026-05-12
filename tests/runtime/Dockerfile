FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY tests/runtime ./tests/runtime

CMD ["sh", "-c", "sleep 15 && python -m unittest discover -s tests/runtime -p 'test_*.py' -v"]
