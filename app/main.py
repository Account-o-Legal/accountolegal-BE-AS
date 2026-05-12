"""
FastAPI application entry point.
OTel setup happens inside lifespan — before the first request is served.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import engine
from app.middleware.tenant import TenantMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.observability.otel import setup_telemetry
from app.observability.logger import setup_logging, get_logger

# Import all module routers
from app.modules.auth.router import router as auth_router
from app.modules.accounting_core.router import router as accounting_router
from app.modules.sales.router import router as sales_router
from app.modules.purchases.router import router as purchases_router
from app.modules.banking.router import router as banking_router
from app.modules.tax.router import router as tax_router
from app.modules.reporting.router import router as reporting_router
from app.modules.currency.router import router as currency_router
from app.modules.files.router import router as files_router
from app.modules.billing.router import router as billing_router
from app.modules.ai.router import router as ai_router
from app.modules.collaboration.router import router as collab_router
from app.modules.automation.router import router as automation_router

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init OTel + logging. Shutdown: flush exporters."""
    setup_logging()
    setup_telemetry(app=app, engine=engine)
    log.info("app_startup", environment=settings.APP_ENV, version=settings.APP_VERSION)
    yield
    log.info("app_shutdown")


app = FastAPI(
    title="Accounting Software API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware (order matters — outermost executes first) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)
app.add_middleware(RateLimitMiddleware)


# ── Global exception handler ───────────────────────────────
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "request_id": request.headers.get("x-request-id", ""),
            }
        },
    )


# ── Health check ───────────────────────────────────────────
@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


# ── Prometheus metrics endpoint ────────────────────────────
# Exposed for Prometheus scraping via opentelemetry-exporter-prometheus
from opentelemetry.exporter.prometheus import PrometheusMetricReader  # noqa
from prometheus_client import make_asgi_app  # noqa
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ── Routers ────────────────────────────────────────────────
API = "/api/v1"

app.include_router(auth_router,        prefix=f"{API}/auth",          tags=["Auth"])
app.include_router(accounting_router,  prefix=f"{API}/accounting",    tags=["Accounting Core"])
app.include_router(sales_router,       prefix=f"{API}/sales",         tags=["Sales"])
app.include_router(purchases_router,   prefix=f"{API}/purchases",     tags=["Purchases"])
app.include_router(banking_router,     prefix=f"{API}/banking",       tags=["Banking"])
app.include_router(tax_router,         prefix=f"{API}/tax",           tags=["Tax"])
app.include_router(reporting_router,   prefix=f"{API}/reports",       tags=["Reporting"])
app.include_router(currency_router,    prefix=f"{API}/currency",      tags=["Currency"])
app.include_router(files_router,       prefix=f"{API}/files",         tags=["Files"])
app.include_router(billing_router,     prefix=f"{API}/billing",       tags=["Billing"])
app.include_router(ai_router,          prefix=f"{API}/ai",            tags=["AI"])
app.include_router(collab_router,      prefix=f"{API}/collaboration",  tags=["Collaboration"])
app.include_router(automation_router,  prefix=f"{API}/automation",    tags=["Automation"])