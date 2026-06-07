# associazione-api

REST API backend for music association management — members, annual subscriptions, and document repository.

[![CI](https://github.com/DevilFlow92/associazione-api/actions/workflows/ci.yml/badge.svg)](https://github.com/DevilFlow92/associazione-api/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

## Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.136+ |
| Language | Python 3.12 |
| ORM | SQLAlchemy 2 (async) |
| Database | PostgreSQL 16 |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| ASGI server | Uvicorn |
| Package manager | uv |
| Shared utilities | [associazione-api-toolkit](https://github.com/DevilFlow92/associazione-api-toolkit) |
| Linting / formatting | Ruff |
| Type checking | mypy |

## Project structure

```text
app/
├── api/v1/
│   ├── soci.py          # Members router
│   ├── iscrizioni.py    # Subscriptions router
│   ├── documenti.py     # Documents router
│   └── templates.py     # Templates router
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # Async engine & session factory
│   ├── logging.py       # Shim → associazione_toolkit.logging
│   ├── middleware.py     # Request ID & timing middleware
│   └── storage.py       # File upload & validation
├── exceptions/          # Domain-specific exceptions
├── models/              # SQLAlchemy models
├── repositories/        # Data access layer
├── schemas/             # Pydantic request/response schemas
└── services/            # Business logic layer
migrations/              # Alembic revisions
tests/
├── unit/
└── integration/
main.py                  # FastAPI app entrypoint
```

The architecture follows a layered pattern: **Router → Service → Repository → Model**.

## API endpoints

Base prefix: `/api/v1`

### Soci

| Method | Path | Description |
|---|---|---|
| `GET` | `/soci/` | List members (paginated) |
| `GET` | `/soci/{id}` | Get a member by ID |
| `POST` | `/soci/` | Create a new member |
| `PATCH` | `/soci/{id}` | Update a member |
| `DELETE` | `/soci/{id}` | Soft delete a member (204) |

### Iscrizioni

| Method | Path | Description |
|---|---|---|
| `GET` | `/iscrizioni/socio/{socio_id}` | Get subscriptions for a member (paginated) |
| `GET` | `/iscrizioni/{id}` | Get a subscription by ID |
| `POST` | `/iscrizioni/` | Create a new subscription |
| `PATCH` | `/iscrizioni/{id}` | Update a subscription |

### Documenti

| Method | Path | Description |
|---|---|---|
| `GET` | `/documenti/` | List documents, filterable by type (paginated) |
| `GET` | `/documenti/socio/{socio_id}` | Get all documents for a member |
| `GET` | `/documenti/{id}` | Get a document by ID |
| `POST` | `/documenti/` | Upload a PDF document |
| `GET` | `/documenti/{id}/download` | Download a document |
| `DELETE` | `/documenti/{id}` | Delete a document (204) |

### Templates

| Method | Path | Description |
|---|---|---|
| `GET` | `/templates/` | List templates, filterable by type (paginated) |
| `GET` | `/templates/{id}` | Get a template by ID |
| `POST` | `/templates/` | Upload a PDF template |
| `PATCH` | `/templates/{id}` | Update template metadata |
| `GET` | `/templates/{id}/download` | Download a template |
| `DELETE` | `/templates/{id}` | Delete a template (204) |

### Health

| Method | Path |
|---|---|
| `GET` | `/health` |

Interactive docs are available at `/docs` (Swagger UI) and `/redoc` when the server is running.

## Paginated responses

All list endpoints return a paginated envelope. Query parameters: `page` (default: 1) and `page_size` (default: 20, max: 100).

```bash
GET /api/v1/soci/?page=1&page_size=10
```

```json
{
  "items": [...],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total_items": 42,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

## Structured logging

Every request is assigned a `request_id` (UUID) via middleware, bound to the async context via `associazione_toolkit.logging`. All log records emitted during a request — including service and repository layers — include the `request_id` automatically.

In development (`APP_ENV=development`) logs are human-readable. In production they are emitted as JSON, ready for Datadog, Loki, or CloudWatch.

```json
{"event": "request completed", "method": "GET", "path": "/api/v1/soci/", "status_code": 200, "duration_ms": 12.4, "request_id": "abc-123", "timestamp": "..."}
```

## Local development

### Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python package manager
- Docker & Docker Compose

### With Docker Compose (recommended)

```bash
docker compose up --build
```

This starts PostgreSQL 16 on port `5432` and the API on port `8000`.

### Without Docker

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Copy and configure the environment file:

   ```bash
   cp .env.example .env
   # edit .env with your DATABASE_URL
   ```

3. Run database migrations:

   ```bash
   uv run alembic upgrade head
   ```

4. Start the server:

   ```bash
   uv run uvicorn main:app --reload
   ```

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/associazione_db` | Async PostgreSQL connection string |
| `APP_ENV` | `development` | Environment name — controls log format (JSON in non-development) |
| `APP_DEBUG` | `true` | Enables debug log level |
| `SECRET_KEY` | `changeme` | Application secret key |

## Database migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Rollback one revision
uv run alembic downgrade -1
```

## Testing

```bash
uv run pytest tests/ -v
```

Test files live under `tests/unit/` and `tests/integration/`.

## Code quality

```bash
# Lint + format
uv run ruff check --fix app/ tests/
uv run ruff format app/ tests/

# Type check
uv run mypy app/
```

## CI/CD

GitHub Actions runs on every push and pull request to `main`:

1. **Lint** — `ruff check`
2. **Format** — `ruff format --check`
3. **Type check** — `mypy`
4. **Tests** — `pytest`

## Roadmap

### Authentication & multi-user access (coming soon)

The API currently has no authentication layer. The planned design separates two distinct authentication planes:

**Machine-to-machine — JWT**
Service accounts for workers, bots, and bulk import services authenticate via JWT tokens. Stateless, long-lived, scoped per service type (e.g. a Celery worker can write data but not manage users).

**Human users — session-based**
Two macro-roles with configurable permissions per association:

- **Amministratori** — consiglio direttivo members, with per-carica permission sets (e.g. tesoriere gets contabilità access, segretario gets verbali and archivio parti, presidente gets everything)
- **Soci standard** — minimal access, self-service only (event attendance)

Credentials are managed natively (email + bcrypt password hash) — no external OAuth2 provider.

The RBAC model is association-configurable, meaning each banda can decide which permissions map to which direttivo role without code changes.

**Planned tables:** `utenti`, `ruoli`, `permessi`, `ruoli_permessi`, `utenti_ruoli`

---

### Other planned features

- Bulk import of members and externals from Excel files (via async worker)
- Event management — processioni, concerti, prove — with attendance tracking
- Receipt generation for externals and event revenues
- Assembly minutes editor with PDF template rendering
- Telegram / email notification service

## Related repositories

| Repository | Description |
|---|---|
| [associazione-api-toolkit](https://github.com/DevilFlow92/associazione-api-toolkit) | Shared utilities — logging, pagination, retry, HTTP client |
| [associazione-api-infra](https://github.com/DevilFlow92/associazione-api-infra) | Infrastructure — Helm charts + Kustomize for Kubernetes |
| **associazione-api** | ← you are here |
