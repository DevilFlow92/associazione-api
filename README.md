# associazione-api

REST API backend for music association management — members and annual subscriptions.

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
| Linting / formatting | Ruff |
| Type checking | mypy (strict off) |

## Project structure

```
app/
├── api/v1/
│   ├── soci.py          # Members router
│   └── iscrizioni.py    # Subscriptions router
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   └── database.py      # Async engine & session factory
├── exceptions/          # Domain-specific exceptions
├── models/
│   ├── socio.py         # Socio SQLAlchemy model
│   └── iscrizione.py    # Iscrizione SQLAlchemy model
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
| `GET` | `/soci/` | List all members |
| `GET` | `/soci/{id}` | Get a member by ID |
| `POST` | `/soci/` | Create a new member |
| `PATCH` | `/soci/{id}` | Update a member |
| `DELETE` | `/soci/{id}` | Delete a member (204) |

### Iscrizioni

| Method | Path | Description |
|---|---|---|
| `GET` | `/iscrizioni/socio/{socio_id}` | Get all subscriptions for a member |
| `GET` | `/iscrizioni/{id}` | Get a subscription by ID |
| `POST` | `/iscrizioni/` | Create a new subscription |
| `PATCH` | `/iscrizioni/{id}` | Update a subscription |

### Health

| Method | Path |
|---|---|
| `GET` | `/health` |

Interactive docs are available at `/docs` (Swagger UI) and `/redoc` when the server is running.

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
| `APP_ENV` | `development` | Environment name |
| `APP_DEBUG` | `true` | Enables SQLAlchemy query logging |
| `SECRET_KEY` | `changeme` | Application secret key |

Copy `.env.example` to `.env` and adjust the values before running locally.

## Database migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Create a new migration after model changes
uv run alembic revision --autogenerate -m "description"

# Rollback one revision
uv run alembic downgrade -1
```

## Code quality

Pre-commit hooks run automatically on every commit (Ruff lint + format, trailing whitespace, YAML checks). To run them manually:

```bash
uv run pre-commit run --all-files
```

Type checking:

```bash
uv run mypy app/
```

## Testing

```bash
uv run pytest
```

Test files live under `tests/unit/` and `tests/integration/`.
