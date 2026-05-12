"""
Named tracer and span helper utilities.
Use create_span() for manual instrumentation of business-critical operations.

Usage:
    from app.observability.tracer import tracer, create_span
    from opentelemetry.trace import SpanKind

    with create_span("accounting.journal_entry.post", attributes={"tenant_id": tid}):
        ...
"""
import functools
import time
from contextlib import contextmanager
from typing import Any, Callable, Generator

from opentelemetry import trace
from opentelemetry.trace import Span, SpanKind, Status, StatusCode

tracer = trace.get_tracer("accounting-software", schema_url="https://opentelemetry.io/schemas/1.11.0")


@contextmanager
def create_span(
    name: str,
    attributes: dict[str, Any] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> Generator[Span, None, None]:
    """
    Context manager that starts a span, attaches attributes,
    and records exceptions automatically.

    with create_span("journal.post", {"tenant_id": tid, "line_count": 2}) as span:
        result = do_work()
        span.set_attribute("entry_id", str(result.id))
    """
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, v)
        try:
            yield span
        except Exception as exc:
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            span.record_exception(exc)
            raise


def instrument(span_name: str, attributes: dict[str, Any] | None = None):
    """
    Decorator for sync and async functions.

    @instrument("accounting.reconciliation.match")
    async def match_transaction(self, txn_id: str) -> None:
        ...
    """
    def decorator(func: Callable):
        if _is_async(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with create_span(span_name, attributes):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with create_span(span_name, attributes):
                    return func(*args, **kwargs)
            return sync_wrapper
    return decorator


def _is_async(func: Callable) -> bool:
    import asyncio
    return asyncio.iscoroutinefunction(func)