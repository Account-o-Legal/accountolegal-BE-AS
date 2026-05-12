"""
Structured JSON logger.
Automatically injects trace_id and span_id from the active OTel span
so every log line links directly to a Tempo trace in Grafana.

Usage:
    from app.observability.logger import get_logger
    log = get_logger(__name__)
    log.info("invoice_paid", invoice_id=str(invoice.id), amount=invoice.total)
"""
import logging
import os
import structlog
from opentelemetry import trace


def _add_otel_context(logger, method, event_dict):
    """Processor: inject trace_id + span_id from the active OTel span."""
    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict


def _add_service_context(logger, method, event_dict):
    """Processor: stamp every log with service name and environment."""
    event_dict["service"] = os.getenv("OTEL_SERVICE_NAME", "accounting-software")
    event_dict["environment"] = os.getenv("APP_ENV", "development")
    return event_dict


def setup_logging() -> None:
    """Call once at app startup."""
    log_level = logging.DEBUG if os.getenv("APP_ENV") != "production" else logging.INFO

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            _add_service_context,
            _add_otel_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),   # pure JSON output
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Redirect stdlib logging (SQLAlchemy, uvicorn, etc.) through structlog
    logging.basicConfig(
        format="%(message)s",
        level=log_level,
        handlers=[structlog.stdlib.ProcessorFormatter.wrap_for_formatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        )],
    )


def get_logger(name: str = __name__):
    """Return a bound structlog logger for the given module name."""
    return structlog.get_logger(name)