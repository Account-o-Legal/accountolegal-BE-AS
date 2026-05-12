"""
All custom application metrics defined in one place.
Import the metric objects you need directly from this module.

Usage:
    from app.observability.metrics import journal_entries_total
    journal_entries_total.add(1, {"tenant_id": tid, "jurisdiction": "PK"})
"""
from opentelemetry import metrics

_meter = metrics.get_meter("accounting-software", version="0.1.0")

# ── Accounting Core ───────────────────────────────────────
journal_entries_total = _meter.create_counter(
    "accounting.journal_entries.total",
    description="Total journal entries posted",
    unit="1",
)

journal_entry_duration = _meter.create_histogram(
    "accounting.journal_entry.duration",
    description="Time to validate and post a journal entry",
    unit="ms",
)

# ── Invoicing ─────────────────────────────────────────────
invoices_created_total = _meter.create_counter(
    "accounting.invoices.created.total",
    description="Total invoices created",
    unit="1",
)

invoices_paid_total = _meter.create_counter(
    "accounting.invoices.paid.total",
    description="Total invoices marked paid",
    unit="1",
)

invoice_amount_histogram = _meter.create_histogram(
    "accounting.invoice.amount",
    description="Distribution of invoice amounts (base currency)",
    unit="PKR",
)

# ── Banking ───────────────────────────────────────────────
bank_transactions_imported_total = _meter.create_counter(
    "accounting.bank_transactions.imported.total",
    description="Total bank transactions imported",
    unit="1",
)

bank_import_failures_total = _meter.create_counter(
    "accounting.bank_import.failures.total",
    description="Bank import failures by reason",
    unit="1",
)

reconciliation_matches_total = _meter.create_counter(
    "accounting.reconciliation.matches.total",
    description="Transactions auto-matched during reconciliation",
    unit="1",
)

# ── AI ────────────────────────────────────────────────────
ai_inference_requests_total = _meter.create_counter(
    "ai.inference.requests.total",
    description="Total LLM inference requests",
    unit="1",
)

ai_inference_duration = _meter.create_histogram(
    "ai.inference.duration",
    description="LLM inference duration",
    unit="ms",
)

ai_tokens_used_total = _meter.create_counter(
    "ai.tokens.used.total",
    description="Total LLM tokens consumed",
    unit="1",
)

ai_cache_hits_total = _meter.create_counter(
    "ai.cache.hits.total",
    description="Semantic cache hits — avoided LLM calls",
    unit="1",
)

ai_anomalies_detected_total = _meter.create_counter(
    "ai.anomalies.detected.total",
    description="Anomalies detected by severity",
    unit="1",
)

# ── HTTP (supplement auto-instrumentation) ────────────────
http_errors_total = _meter.create_counter(
    "http.errors.total",
    description="HTTP 4xx and 5xx responses by route",
    unit="1",
)

# ── Queue ─────────────────────────────────────────────────
queue_jobs_enqueued_total = _meter.create_counter(
    "queue.jobs.enqueued.total",
    description="Jobs enqueued by type",
    unit="1",
)

queue_job_duration = _meter.create_histogram(
    "queue.job.duration",
    description="Job execution time by type",
    unit="ms",
)

queue_job_failures_total = _meter.create_counter(
    "queue.job.failures.total",
    description="Failed jobs by type",
    unit="1",
)

# ── Tax ───────────────────────────────────────────────────
tax_transactions_total = _meter.create_counter(
    "accounting.tax.transactions.total",
    description="Tax transactions recorded by jurisdiction and tax code",
    unit="1",
)