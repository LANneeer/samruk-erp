import time
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST


REQS = Counter("http_requests_total", "Total HTTP requests", ["method","path","status"])
LAT  = Histogram("http_request_duration_seconds", "Latency", ["method","path","status"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        dur = time.perf_counter() - start
        REQS.labels(request.method, request.url.path, response.status_code).inc()
        LAT.labels(request.method, request.url.path, response.status_code).observe(dur)
        return response


def prom_endpoint():
    data = generate_latest()
    return data, CONTENT_TYPE_LATEST
