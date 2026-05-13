import logging
import traceback
from logstash_async.formatter import LogstashFormatter
from logstash_async.handler import AsynchronousLogstashHandler
from typing import Any
import contextvars, uuid

# we put most info in 'extra' argument of log functions for logstash, 
# but for console logger by default doesn't show 'extra' fields, 
# so we create a custom formatter to extract all additional fields to a
# console-only attribute and access it in format string as %(console_extra)s.
# Using the name "extra" here breaks logstash_async because that formatter
# expects its own structured "extra" object.
class ExtraFieldsFormatter(logging.Formatter):
    def format(self, record):
        # standard LogRecord attributes
        standard_attrs = logging.LogRecord(
            name='', level=0, pathname='', lineno=0,
            msg='', args=(), exc_info=None
        ).__dict__.keys()

        # extract extra fields
        extra_lines = {
            f"\n\t\t  {k}: {v}" for k, v in record.__dict__.items()
            if k not in standard_attrs
        }

        record.console_extra = ''.join(extra_lines)  # attach for console formatter
        return super().format(record)


console_formatter = ExtraFieldsFormatter("%(levelname)s:\t%(message)s%(console_extra)s")
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
handlers = [console_handler]

audit_logger = logging.getLogger("audit")
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

def init_logging(log_level: str, logstash_host: str = None, logstash_port: int = None):
    if logstash_host and logstash_port:
        logstash_handler = AsynchronousLogstashHandler(
            host=logstash_host, port=logstash_port, database_path=None
        )
        logstash_handler.setFormatter(LogstashFormatter())
        handlers.append(logstash_handler)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        handlers=handlers,
    )



def log_exception(logger: logging.Logger, exc: Exception, limit: int = 10) -> None:
    # get stack trace
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__, chain=False)
    # limit to n frames
    trace_str = "".join(tb[-limit:])
    # print to log
    logger.error("Unhandled exception (truncated)\n" + trace_str)


# def extract_request_id(request: Request, request_id_header: str) -> str:
#     rid = request.headers.get(request_id_header) or str(uuid.uuid4())
#     request_id_ctx.set(rid)
#     return rid

def get_request_id() -> str:
    rid = request_id_ctx.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_ctx.set(rid)
    return rid

def audit_log(
    *,
    action: str,
    actor_id: str | None,
    target: str | None,
    status: str,
    meta: dict[str, Any] | None = None,
) -> None:
    payload = {
        "action": action,
        "actor_id": actor_id,
        "target": target,
        "status": status,
        "meta": meta or {},
    }
    audit_logger.info("audit", extra={"request_id": get_request_id(), "audit": payload})
