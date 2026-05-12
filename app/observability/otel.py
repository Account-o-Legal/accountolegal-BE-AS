"""
OpenTelemetry SDK initialisation.
Call setup_telemetry() once at app startup (lifespan).
"""
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
import logging


def setup_telemetry(app=None, engine=None) -> None:
    """
    Initialise traces, metrics, and logs. Wire up auto-instrumentation.
    Call this inside FastAPI lifespan before the app starts serving.
    """
    environment = os.getenv("APP_ENV", "development")
    service_name = os.getenv("OTEL_SERVICE_NAME", "accounting-software")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: os.getenv("APP_VERSION", "0.1.0"),
        "deployment.environment": environment,
    })

    # ── Traces ────────────────────────────────────────────
    # 100% sampling in dev/staging; 10% in prod (errors always sampled)
    sampler = (
        ParentBased(root=TraceIdRatioBased(0.1))
        if environment == "production"
        else ParentBased(root=TraceIdRatioBased(1.0))
    )

    tracer_provider = TracerProvider(resource=resource, sampler=sampler)
    tracer_provider.add_span_processor(
        # BatchSpanProcessor buffers and exports in background
        __import__(
            "opentelemetry.sdk.trace.export",
            fromlist=["BatchSpanProcessor"]
        ).BatchSpanProcessor(
            OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        )
    )
    trace.set_tracer_provider(tracer_provider)

    # ── Metrics ───────────────────────────────────────────
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True),
        export_interval_millis=15_000,
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # ── Logs ──────────────────────────────────────────────
    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(
            OTLPLogExporter(endpoint=otlp_endpoint, insecure=True)
        )
    )
    # Bridge Python's stdlib logging → OTel logs
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    logging.getLogger().addHandler(handler)

    # ── Auto-instrumentation ──────────────────────────────
    if app:
        FastAPIInstrumentor.instrument_app(
            app,
            excluded_urls="health,metrics,docs,redoc,openapi.json",
            server_request_hook=_server_request_hook,
        )

    if engine:
        SQLAlchemyInstrumentor().instrument(
            engine=engine,
            enable_commenter=True,    # adds SQL comments with trace context
        )

    RedisInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()


def _server_request_hook(span, scope):
    """Attach tenant_id to every incoming request span."""
    request = scope.get("app", {})
    state = getattr(request, "state", None)
    if state and hasattr(state, "tenant_id"):
        span.set_attribute("tenant.id", state.tenant_id)