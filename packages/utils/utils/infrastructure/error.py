from fastapi import FastAPI, status, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from utils.domains.common import exceptions as ex
from utils.infrastructure.logging import log_exception


def install_exception_handlers(app: FastAPI, logger: logging.Logger) -> None:
    # disable uvicorn's default error logging to avoid duplicate logs, we'll handle logging ourselves
    uvicorn_logger = logging.getLogger("uvicorn.error")
    uvicorn_logger.setLevel(logging.CRITICAL)
    uvicorn_logger.propagate = False

    custom_exc_list = [
        ex.DuplicateEmail,
        ex.DuplicateUsername,
        ex.Conflict,
        ex.DatabaseConflict,
        ex.NotFound,
        ex.ValidationFailed,
        ex.Unauthorized,
        ex.Forbidden,
        ex.NotSupported,
        ex.DomainError # catch-all for domain errors without specific type
    ]

    # set http codes for our custom exceptions
    for exc_type in custom_exc_list:
        @app.exception_handler(exc_type)
        async def custom_exception_handler(request: Request, exc: Exception):
            cid = getattr(request.state, "correlation_id", None)
            log_exception(logger, exc)
            return JSONResponse(
                status_code=getattr(exc, "status_code", status.HTTP_500_INTERNAL_SERVER_ERROR),
                content={
                    "error": {
                        "type": exc.__class__.__name__,
                        "code": getattr(exc, "code", "undefined_code"),
                        "message": str(exc) or exc.__class__.__name__,
                        "correlation_id": cid,
                    }
                },
            )

    # it is not handled as exception in FastAPI by default
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        cid = getattr(request.state, "correlation_id", None)
        log_exception(logger, exc)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {
                "type": exc.__class__.__name__,
                "code": "http_exception",
                "message": exc.detail,
                "correlation_id": cid,
            }},
        )
    
    # handle all other expections
    @app.exception_handler(Exception)
    async def other_exception_handler(request: Request, exc: Exception):
        cid = getattr(request.state, "correlation_id", None)
        log_exception(logger, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {
                "type": exc.__class__.__name__,
                "code": "internal_error",
                "message": str(exc),
                "correlation_id": cid,
            }},
        )
