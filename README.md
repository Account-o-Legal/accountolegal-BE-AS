# Accounting Software

A production-grade, multi-tenant SaaS accounting platform built with **FastAPI**. Launched in Pakistan, architected for global expansion. Features double-entry accounting, AI-powered financial insights, bank reconciliation, tax compliance, and a full observability stack via OpenTelemetry + Grafana.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development](#local-development)
  - [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Running Workers](#running-workers)
- [Database Migrations](#database-migrations)
- [Testing](#testing)
- [Observability](#observability)
- [API Reference](#api-reference)
- [Module Overview](#module-overview)
- [Branch Strategy](#branch-strategy)
- [Deployment](#deployment)
- [Jurisdiction Packs](#jurisdiction-packs)
- [Roadmap](#roadmap)

---

## Features

- **Double-Entry Accounting Engine** — enforced balance checks, immutable journal entries, period management
- **Invoicing & Bills** — full lifecycle management, AR/AP aging, credit notes, PDF generation
- **Banking & Reconciliation** — CSV/OFX import, smart auto-matching rules
- **Tax & Compliance** — FBR GST (Pakistan), jurisdiction-aware tax rules, append-only audit log
- **Financial Reporting** — P&L, Balance Sheet, Cash Flow, Trial Balance (JSON / CSV / PDF)
- **Multi-Currency** — manual rates (MVP), live feed integration (V2), FX gain/loss calculation
- **AI Layer** — transaction explainability, anomaly detection, cash-flow coaching, pricing assistant
- **Automation Engine** — trigger/action workflows, marketplace templates (V3)
- **Collaboration** — comment threads, approval workflows, accountant handoff (V2)
- **Observability** — OpenTelemetry traces + Prometheus metrics + Loki logs → Grafana dashboards
- **Multi-Tenant** — workspace isolation, row-level security, jurisdiction-aware data model
- **Pakistan-first** — JazzCash/EasyPaisa, Urdu locale support, FBR compliance, ICAP verification

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| Migrations | Alembic |
| Cache / Queue | Redis 7 + ARQ |
| Object Storage | AWS S3 / MinIO (aioboto3) |
| AI / LLM | Anthropic Claude API |
| Embeddings | OpenAI text-embedding-3-small |
| PDF Generation | WeasyPrint + Jinja2 |
| Auth | python-jose (JWT) + passlib (bcrypt) + pyotp (2FA) |
| Validation | Pydantic v2 + pydantic-settings |
| Observability | OpenTelemetry SDK + Grafana (Tempo · Loki · Prometheus) |
| Logging | structlog (structured JSON) |
| Payments (PK) | JazzCash · EasyPaisa · Stripe |
| Testing | pytest + pytest-asyncio + factory-boy |
| Linting | Ruff + mypy |

---

## Project Structure

```
accounting-software/
├── app/
│   ├── main.py                  # FastAPI app init, router registration, lifespan
│   ├── dependencies.py          # Shared Depends() — db session, current user, tenant
│   │
│   ├── core/                    # Cross-cutting concerns (no business logic)
│   │   ├── config.py            # pydantic-settings, env vars, jurisdiction packs
│   │   ├── security.py          # JWT, password hashing, TOTP
│   │   ├── exceptions.py        # AppException, NotFoundError, ValidationError
│   │   ├── pagination.py        # Cursor-based pagination helpers
│   │   └── enums.py             # Shared Enum types
│   │
│   ├── db/
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   ├── session.py           # async_sessionmaker, get_db() dependency
│   │   └── mixins.py            # TenantMixin, TimestampMixin, ULIDMixin
│   │
│   ├── middleware/
│   │   ├── tenant.py            # Inject tenant_id from JWT into request.state
│   │   ├── idempotency.py       # Idempotency-Key deduplication
│   │   └── rate_limit.py        # Per-tenant + per-IP rate limiting
│   │
│   ├── observability/
│   │   ├── otel.py              # SDK init, auto-instrumentation
│   │   ├── metrics.py           # Custom counters and histograms
│   │   ├── tracer.py            # Named tracer, span helpers
│   │   └── logger.py            # structlog JSON logger with trace_id injection
│   │
│   ├── modules/                 # One sub-package per bounded context
│   │   ├── auth/                # Login, register, JWT, 2FA, RBAC
│   │   ├── accounting_core/     # CoA, double-entry engine, periods, ledger
│   │   ├── sales/               # Invoices, credit notes, contacts
│   │   ├── purchases/           # Bills, expenses, vendors
│   │   ├── banking/             # Bank accounts, CSV/OFX import, reconciliation
│   │   ├── tax/                 # Tax rates, FBR compliance, audit log
│   │   ├── reporting/           # P&L, Balance Sheet, Cash Flow, exports
│   │   ├── currency/            # Exchange rates, FX adjustments
│   │   ├── files/               # S3 upload, presigned URLs, virus scan
│   │   ├── billing/             # Subscription plans, payments, feature gates
│   │   ├── notifications/       # Email, SMS, push + locale templates
│   │   ├── ai/                  # AI gateway, explainability, anomaly, coaching
│   │   ├── automation/          # Workflow engine, marketplace (V3)
│   │   └── collaboration/       # Comments, approvals, handoff (V2)
│   │
│   └── workers/                 # ARQ async job queue workers
│       ├── main.py              # WorkerSettings, queue registration
│       ├── report_worker.py     # PDF/CSV report generation
│       ├── import_worker.py     # Bank statement processing
│       ├── ai_worker.py         # LLM inference jobs
│       ├── notification_worker.py
│       └── anomaly_worker.py    # Nightly anomaly scan
│
├── alembic/                     # Database migrations
│   └── versions/
│
├── config/
│   └── jurisdictions/
│       ├── pk.json              # Pakistan (launch)
│       ├── ae.json              # UAE (V3)
│       └── gb.json              # UK (V3)
│
├── infra/
│   ├── k8s/                     # Kubernetes manifests
│   ├── observability/           # OTel Collector, Prometheus, Loki, Tempo configs
│   └── grafana/
│       ├── dashboards/          # JSON dashboard files (auto-provisioned)
│       └── alerts/              # Alert rule YAML files
│
├── tests/
│   ├── conftest.py              # pytest fixtures, test DB setup
│   ├── fixtures/                # tenant_factory, user_factory, account_factory
│   ├── integration/             # Full HTTP + DB tests
│   └── e2e/                     # Critical user flow tests
│
├── .env.example
├── docker-compose.yml
├── docker-compose.observability.yml
├── Dockerfile
├── alembic.ini
├── pyproject.toml
└── requirements.txt
```

Each module follows the same internal structure:

```
modules/auth/
├── __init__.py
├── router.py       # APIRouter — all endpoints for this module
├── service.py      # Business logic
├── repository.py   # DB queries (SQLAlchemy)
├── schemas.py      # Pydantic request/response models
├── models.py       # SQLAlchemy ORM models
├── dependencies.py # Module-specific Depends()
└── tests.py
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 16
- Redis 7
- Docker + Docker Compose (recommended for local dev)

### Local Development

**1. Clone and enter the project:**
```bash
git clone https://github.com/your-org/accounting-software.git
cd accounting-software
git checkout develop
```

**2. Create and activate virtual environment:**
```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Copy and configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your local values
```

**5. Start infrastructure (PostgreSQL + Redis + Observability):**
```bash
docker compose up -d
```

**6. Run database migrations:**
```bash
alembic upgrade head
```

**7. Start the API server:**
```bash
uvicorn app.main:app --reload --port 8000
```

API is live at: `http://localhost:8000`
Interactive docs: `http://localhost:8000/docs`
ReDoc: `http://localhost:8000/redoc`

---

### Environment Variables

```env
# App
APP_ENV=development
SECRET_KEY=your-secret-key-min-32-chars
ALLOWED_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/accounting

# Redis
REDIS_URL=redis://localhost:6379/0

# AWS S3 / MinIO
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=accounting-files
AWS_S3_REGION=ap-south-1

# AI
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Notifications
RESEND_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_FROM_NUMBER=

# Payments
STRIPE_SECRET_KEY=
JAZZCASH_MERCHANT_ID=
EASYPAISA_STORE_ID=

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
OTEL_SERVICE_NAME=accounting-software
```

---

## Running the App

**Development (with auto-reload):**
```bash
uvicorn app.main:app --reload --port 8000
```

**Production:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Via Docker:**
```bash
docker compose up app
```

---

## Running Workers

ARQ workers handle all async jobs — report generation, bank imports, AI inference, notifications.

**Start all workers:**
```bash
arq app.workers.main.WorkerSettings
```

**Start a specific worker in development:**
```bash
arq app.workers.report_worker.WorkerSettings
```

---

## Database Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Create a new migration after changing models
alembic revision --autogenerate -m "add invoices table"

# Downgrade one step
alembic downgrade -1

# View migration history
alembic history
```

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=term-missing

# Run a specific module
pytest tests/integration/test_invoices.py -v

# Run only unit tests (fast)
pytest -m "not integration" -v
```

Test database is spun up automatically via Docker using the `conftest.py` fixtures. Each test runs in a transaction that is rolled back after the test — no cleanup needed.

---

## Observability

**Start the full observability stack:**
```bash
docker compose -f docker-compose.observability.yml up -d
```

| Service | URL |
|---|---|
| Grafana | http://localhost:3000 (admin / admin) |
| Prometheus | http://localhost:9090 |
| Tempo (traces) | http://localhost:3200 |
| Loki (logs) | http://localhost:3100 |
| OTel Collector | grpc://localhost:4317 |

**Pre-built Grafana dashboards** (auto-provisioned from `infra/grafana/dashboards/`):

- **Platform Overview** — request rate, error rate, P95 latency, queue depth
- **Accounting Core** — journal entries/min, ledger balance checks, period status
- **AI Operations** — inference requests, token usage, cache hit rate
- **Tenant Activity** — active workspaces, invoices created, feature usage
- **Infrastructure** — DB connections, Redis memory, pod health
- **Incident Response** — top error traces (linked to Tempo), slow queries

Every HTTP response includes `X-Request-Id` which maps directly to a Tempo trace — paste it into Grafana Explore to get the full distributed trace.

---

## API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs available at `/docs` (Swagger UI) and `/redoc`.

**Authentication:**
```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
POST /api/v1/auth/login/phone
```

All protected endpoints require:
```
Authorization: Bearer <access_token>
```

**Idempotent writes** — include on all POST requests that should not be duplicated:
```
Idempotency-Key: <unique-uuid>
```

---

## Module Overview

| Module | Phase | Description |
|---|---|---|
| `auth` | MVP | Registration, login (email + phone OTP), JWT, 2FA, RBAC |
| `accounting_core` | MVP | Chart of accounts, double-entry engine, journal entries, periods |
| `sales` | MVP | Invoices, credit notes, customer contacts, AR aging |
| `purchases` | MVP | Bills, expenses, vendor contacts, AP aging |
| `banking` | MVP | Bank accounts, CSV/OFX import, manual reconciliation |
| `tax` | MVP | FBR GST, tax rates, compliance reports, audit log |
| `reporting` | MVP | P&L, Balance Sheet, Cash Flow, Trial Balance, exports |
| `currency` | MVP | Exchange rates, FX gain/loss calculation |
| `files` | MVP | S3 upload, presigned URLs, virus scanning |
| `billing` | MVP | Plans (PKR), JazzCash/EasyPaisa/Stripe, feature gates |
| `notifications` | MVP | Email (Resend), SMS (Twilio), Urdu templates |
| `ai` | MVP→V3 | Explainability (MVP), anomaly detection (V2), coaching (V3) |
| `collaboration` | V2 | Comment threads, approval workflows, handoff checklists |
| `automation` | V3 | Trigger/action workflows, community marketplace |

---

## Branch Strategy

```
main          ← production (protected, auto-deploys)
  └── staging ← QA + E2E tests gate
        └── develop ← integration branch for all features
              ├── feat/auth
              ├── feat/accounting-core
              ├── feat/invoicing
              ├── feat/banking
              ├── feat/ai
              └── feat/observability
```

**Rules:**
- `main` — no direct push; requires 1 approval + all CI checks green
- `staging` — merges from `develop` via release branch; E2E tests must pass
- `develop` — all feature PRs target here; requires 1 approval + unit tests green
- `feat/*` — branch off `develop`; squash merge back
- `hotfix/*` — branch off `main`; merge back to `main` AND `develop`

---

## Deployment

**Docker build:**
```bash
docker build -t accounting-software:latest .
```

**Kubernetes:**
```bash
kubectl apply -f infra/k8s/
```

**Grafana dashboards** are provisioned automatically from `infra/grafana/dashboards/` — never edit them in the UI directly. All changes go through the JSON files in the repo.

**CI/CD pipeline** (GitHub Actions → ArgoCD):
1. `ci.yml` — runs on every PR to `develop`: lint (Ruff), type check (mypy), unit tests
2. `integration.yml` — runs on merge to `staging`: full test suite + Docker build
3. `deploy.yml` — runs on merge to `main`: triggers ArgoCD sync to production cluster

---

## Jurisdiction Packs

Adding a new country is a **config change, not a code change**.

Each jurisdiction pack (`config/jurisdictions/pk.json`) defines:

```json
{
  "code": "PK",
  "name": "Pakistan",
  "currency": "PKR",
  "locales": ["en-PK", "ur-PK"],
  "rtl_locales": ["ur-PK"],
  "tax_system": "FBR",
  "fiscal_year_start_month": 7,
  "date_format": "DD/MM/YYYY",
  "payment_methods": ["jazzcash", "easypaisa", "bank_transfer", "card"],
  "default_coa_template": "pk-standard",
  "active": true
}
```

To add UAE: create `config/jurisdictions/ae.json`, add the CoA template, configure payment methods, deploy. No code changes required.

---

## Roadmap

**MVP (Months 1–4)**
- [x] Project scaffolding and CI/CD pipeline
- [ ] Auth — email + phone OTP, JWT, RBAC
- [ ] Accounting core — double-entry engine, CoA, periods
- [ ] Sales & Purchases — invoicing, bills, AR/AP aging
- [ ] Banking — CSV/OFX import, manual reconciliation
- [ ] Tax — FBR GST, audit log
- [ ] Reporting — P&L, Balance Sheet, Cash Flow
- [ ] AI — transaction explainability
- [ ] Full OTel + Grafana observability stack
- [ ] Billing — PKR plans, JazzCash + EasyPaisa

**V2 (Months 5–10)**
- [ ] Auto bank feeds + smart categorization rules
- [ ] AI anomaly detection + audit assistant
- [ ] Budget vs actual reporting + visual cash flow
- [ ] Comment threads + approval workflows
- [ ] Payment gateway webhook reconciliation
- [ ] Industry CoA packs (agencies, restaurants, freelancers)

**V3 (Months 11–18)**
- [ ] Cash-flow coaching AI + 30/60/90-day forecasting
- [ ] Automation marketplace
- [ ] Multi-entity consolidation (Enterprise)
- [ ] Dispute bundle export
- [ ] UAE + UK jurisdiction packs
- [ ] Multi-region data residency

---

## Contributing

1. Fork the repository
2. Create a feature branch off `develop`: `git checkout -b feat/your-feature`
3. Commit with conventional commits: `feat:`, `fix:`, `chore:`, `docs:`
4. Push and open a PR targeting `develop`
5. Ensure all CI checks pass before requesting review

---

**Built by Bridge Homies**
info@bridgehomies.com | +92 342 9263395 | 167A, Block G-1, Johar Town, Lahore