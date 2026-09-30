FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY tests/runtime ./tests/runtime

# without [] and "exec" the container stop will be stopping for 10 seconds
CMD ["sh", "-c", "\
    sleep 15 && \
    exec python -m unittest discover \
        -s tests/runtime \
        -p 'test_*.py' \
        -v \
"]
