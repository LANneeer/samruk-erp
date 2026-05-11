import asyncio
import json
import logging
import zlib
from dataclasses import dataclass
from typing import Optional, Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis

logger = logging.getLogger("cached")


@dataclass
class CachedResponse:
    status: int
    headers: dict[str, str]
    body: bytes

    def to_bytes(self) -> bytes:
        payload = json.dumps({
            "status": self.status,
            "headers": self.headers,
            "body": self.body.decode("utf-8", "ignore"),
        }).encode("utf-8")
        return zlib.compress(payload)

    @staticmethod
    def from_bytes(b: bytes) -> "CachedResponse":
        data = json.loads(zlib.decompress(b).decode("utf-8"))
        return CachedResponse(
            status=data["status"],
            headers=data["headers"],
            body=data["body"].encode("utf-8"),
        )


def make_key(request: Request) -> str:
    header_key = request.headers.get("Idempotency-Key", "")
    return f"idem:{request.method}:{request.url.hostname}:{request.url.port}:{request.url.path}:{header_key}"


class IdempotencyMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        redis_url: str,
        ttl_sec: int,
        max_body_bytes: int,
        get_request_id: Optional[Callable[[], str]] = None,
    ):
        super().__init__(app)
        self.redis_url = redis_url
        self.ttl_sec = ttl_sec
        self.max_body_bytes = max_body_bytes
        self.get_request_id = get_request_id
        self.redis: Optional[Redis] = None
        self._init_lock = asyncio.Lock()

    async def _ensure(self):
        if self.redis is None:
            async with self._init_lock:
                if self.redis is None:
                    self.redis = await Redis.from_url(self.redis_url, encoding="utf-8", decode_responses=False)

    async def dispatch(self, request: Request, call_next):
        await self._ensure()

        if request.method not in ("GET", "HEAD", "DELETE"):
            return await call_next(request)

        # try get cached response
        key = make_key(request)
        cached = await self.redis.get(key)
        if cached:
            cr = CachedResponse.from_bytes(cached)
            extra = {"audit": {"idempotency": "hit","key": key}}
            if self.get_request_id:
                extra["request_id"] = self.get_request_id()
            logger.info("Idempotency hit", extra=extra)
            return Response(content=cr.body, status_code=cr.status, headers=cr.headers)

        # get new response
        response: Response = await call_next(request)

        # return early if content-length is too large or undefined
        content_length = response.headers.get("content-length")
        if content_length is not None:
            try:
                content_length = int(content_length)
            except ValueError:
                content_length = None
            if content_length is None or content_length > self.max_body_bytes:
                extra = {"audit": {"idempotency": "skip", "key": key, "reason": "content-length too large"}}
                if self.get_request_id:
                    extra["request_id"] = self.get_request_id()
                logger.info("Idempotency skip", extra=extra)
                return response

        # read body into memory
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
        new_resp = Response(content=body, status_code=response.status_code, headers=dict(response.headers))

        # save response to cache
        cr = CachedResponse(status=new_resp.status_code, headers=dict(new_resp.headers), body=body)
        await self.redis.setex(key, self.ttl_sec, cr.to_bytes())
        extra = {"audit": {"idempotency": "store","key": key}}
        if self.get_request_id:
            extra["request_id"] = self.get_request_id()
        logger.info("Idempotency store", extra=extra)
        return new_resp
