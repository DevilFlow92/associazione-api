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
├── api/
│   ├── deps.py          # Auth dependencies (current user, permission guards)
│   └── v1/
│       ├── auth.py      # Login/logout (sessions), JWT issuance, /me
│       ├── utenti.py    # Users router (humans & service accounts)
│       ├── ruoli.py     # Roles router (RBAC)
│       ├── permessi.py  # Permissions catalogue (read-only)
│       ├── persone.py   # People (anagrafica) router + addresses (M2M)
│   ├── indirizzi.py     # Addresses router
│   ├── contatti.py      # Contacts router
│   ├── soci.py          # Members router
│   ├── esterni.py       # Externals router
│   ├── iscrizioni.py    # Annual subscriptions router
│   ├── servizi.py       # Events router (filterable by year)
│   ├── ricevute.py      # Receipts router
│   ├── voci_contabilita.py  # Accounting items router
│   ├── flussi_cassa.py  # Cash-flow movements router
│   ├── stati.py …       # Lookup routers (states, regions, provinces,
│   │                    #   municipalities, instruments, address types,
│   │                    #   bands, contact/band roles, rendiconto sections/
│   │                    #   items/sub-items, cash-flow natures,
│   │                    #   document types, score types, subscription states)
│   ├── documenti.py     # Documents router (file repository)
│   ├── spartiti.py      # Scores router
│   └── templates.py     # Templates router
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # Async engine & session factory
│   ├── logging.py       # Shim → associazione_toolkit.logging
│   ├── middleware.py     # Request ID & timing middleware
│   ├── security.py      # Password hashing, JWT, session tokens
│   └── storage.py       # File upload & validation
├── exceptions/          # Domain-specific exceptions
├── models/              # SQLAlchemy models (lookups.py + entity modules)
├── repositories/        # Data access layer (lookup.py = generic lookup CRUD)
├── schemas/             # Pydantic request/response schemas
└── services/            # Business logic layer (lookup.py = generic lookup CRUD)
migrations/              # Alembic revisions
tests/
├── unit/
└── integration/
main.py                  # FastAPI app entrypoint
```

The architecture follows a layered pattern: **Router → Service → Repository → Model**.

### Domain model

The schema mirrors the association's legacy database (`legacy_db/`). Core
anagrafica entities — **Persona**, **Indirizzo**, **Contatto**, **Socio**,
**Esterno** — are backed by **dimension (lookup) tables** (`Stato`, `Regione`,
`Provincia`, `Comune`, `Strumento`, `TipoIndirizzo`, `Banda`, `RuoloContatto`,
`RuoloBanda`, plus the rendiconto lookups `SezioneRendiconto`, `VoceRendiconto`,
`SottovoceRendiconto`, `NaturaFlusso`, and the documentary lookups
`TipoDocumento`, `TipoSpartito`, `StatoIscrizione`). A person can hold several
addresses (many-to-many via `persone_indirizzi`); a band can hold several
addresses too (`bande_indirizzi`). All 16 lookup tables share a generic CRUD
stack (`repositories/lookup.py`, `services/lookup.py`) to avoid duplication.

**Iscrizione** models a member's annual subscription: each socio must subscribe
once per year (unique constraint on `socio_id` + `anno`), with a participation
quota, a payment state, and optional references to the membership document and
the receipt issued for the payment.

Events and receipts are modelled by **Servizio** (T_Servizi) and **Ricevuta**
(T_Ricevute). A receipt can cover either an external performer's fee for a
service (`servizio_id` + `esterno_id`) or a member's annual subscription quota
(both fields null, referenced from `Iscrizione`).

**Spartito** archives a musical score: it links to a `Documento` (the PDF file),
a score type (marcia festiva, inno religioso, …), an optional instrument (null
means a single PDF containing all parts), and optional physical location
(scaffale / ripiano / cartella).

**Documento** is a pure file archive — a PDF repository decoupled from the
membership model, classified by `TipoDocumento`. Other aggregates (Spartito,
Iscrizione, Ricevuta, Template) reference documents by FK.

**Template** is a lightweight metadata record pointing to a `Documento`. It is
the foundation of a future dynamic-document system (field configurator + frontend
renderer for receipts, annual reports, etc.).

Accounting (contabilità) is modelled by **VoceContabilita** (S_VoceContabilita —
a band's chart-of-accounts line, classified by rendiconto section/item/sub-item)
and **FlussoCassa** (T_FlussoCassa — cash movements against an accounting item,
with a sign and a cash/bank nature).

## API endpoints

Base prefix: `/api/v1`

### Persone (anagrafica)

| Method | Path | Description |
|---|---|---|
| `GET` | `/persone/` | List people (paginated) |
| `GET` | `/persone/{id}` | Get a person by ID |
| `POST` | `/persone/` | Create a new person |
| `PATCH` | `/persone/{id}` | Update a person |
| `DELETE` | `/persone/{id}` | Delete a person (204; 409 if still a socio/esterno) |
| `GET` | `/persone/{id}/indirizzi` | List a person's addresses |
| `PUT` | `/persone/{id}/indirizzi/{indirizzo_id}` | Link an address to a person |
| `DELETE` | `/persone/{id}/indirizzi/{indirizzo_id}` | Unlink an address (204) |

### Indirizzi · Contatti · Soci · Esterni · Iscrizioni

Each exposes standard CRUD under its prefix (`/indirizzi`, `/contatti`, `/soci`,
`/esterni`, `/iscrizioni`): `GET /` (paginated list), `GET /{id}`, `POST /`,
`PATCH /{id}`, `DELETE /{id}` (204). In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/contatti/persona/{persona_id}` | Contacts for a person (paginated) |
| `GET` | `/iscrizioni/?socio_id={id}` | Subscriptions for a member (paginated) |
| `GET` | `/iscrizioni/?anno={anno}` | Subscriptions for a given year (paginated) |

`Socio` and `Esterno` require an existing `persona_id` (404 otherwise) and reject
duplicate codes (409). `Contatto` requires an existing `persona_id`.
`Iscrizione` requires an existing `socio_id` (404) and rejects duplicate
`(socio_id, anno)` pairs (409 — one subscription per member per year).

### Servizi · Ricevute (events & receipts)

Standard CRUD under `/servizi` and `/ricevute`. In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/servizi/?anno={anno}` | List events, filterable by year (paginated) |
| `GET` | `/ricevute/servizio/{servizio_id}` | Receipts for an event (paginated) |

`Servizio` requires an existing `indirizzo_id` (404), and cannot be deleted while
it has receipts (409). `Ricevuta` supports two use cases: an external
performer's fee (`servizio_id` + `esterno_id`, both validated if provided) and a
member's subscription receipt (both omitted, referenced from `Iscrizione`).

### Contabilità (accounting)

Standard CRUD under `/voci-contabilita` and `/flussi-cassa`. In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/voci-contabilita/?banda_codice={codice}` | Accounting items, filterable by band |
| `GET` | `/flussi-cassa/voce-contabilita/{voce_id}` | Cash movements for an accounting item |

A `VoceContabilita` cannot be deleted while it has cash movements (409). A
`FlussoCassa` requires an existing `voce_contabilita_id` (404 otherwise).

### Tabelle dimensione (lookups)

Reference data with full CRUD, keyed by `codice`. Prefixes: `/stati`,
`/regioni`, `/province`, `/comuni`, `/strumenti`, `/tipi-indirizzo`, `/bande`,
`/ruoli-contatto`, `/ruoli-banda`, `/sezioni-rendiconto`, `/voci-rendiconto`,
`/sottovoci-rendiconto`, `/nature-flusso`, `/tipi-documento`, `/tipi-spartito`,
`/stati-iscrizione`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/{lookup}/` | List entries (paginated) |
| `GET` | `/{lookup}/{codice}` | Get an entry by code |
| `POST` | `/{lookup}/` | Create an entry (409 on duplicate code) |
| `PATCH` | `/{lookup}/{codice}` | Update an entry |
| `DELETE` | `/{lookup}/{codice}` | Delete an entry (204) |

`Banda` additionally manages its addresses (many-to-many):

| Method | Path | Description |
|---|---|---|
| `GET` | `/bande/{codice}/indirizzi` | List a band's addresses |
| `PUT` | `/bande/{codice}/indirizzi/{indirizzo_id}` | Link an address to a band |
| `DELETE` | `/bande/{codice}/indirizzi/{indirizzo_id}` | Unlink an address (204) |

### Documenti

A pure file archive — PDF documents classified by `tipo_documento_codice`,
decoupled from the membership model.

| Method | Path | Description |
|---|---|---|
| `GET` | `/documenti/` | List documents (paginated, filterable by `tipo_documento_codice`) |
| `GET` | `/documenti/{id}` | Get a document by ID |
| `POST` | `/documenti/?tipo_documento_codice={codice}` | Upload a PDF document |
| `GET` | `/documenti/{id}/download` | Download a document (404 if file missing) |
| `DELETE` | `/documenti/{id}` | Delete a document and its file (204) |

### Spartiti

Archives musical scores. Each spartito links to a `Documento` (the PDF), a score
type, and optionally an instrument (`strumento_codice` null = single PDF with all
parts) and physical location.

| Method | Path | Description |
|---|---|---|
| `GET` | `/spartiti/` | List scores (paginated, filterable by `tipo_spartito_codice` / `strumento_codice`) |
| `GET` | `/spartiti/{id}` | Get a score by ID |
| `POST` | `/spartiti/` | Create a score record |
| `PATCH` | `/spartiti/{id}` | Update score metadata |
| `DELETE` | `/spartiti/{id}` | Delete a score record (204) |

### Templates

Lightweight metadata pointing to a `Documento`. Foundation of the future
dynamic-document system (field configurator + frontend renderer).

| Method | Path | Description |
|---|---|---|
| `GET` | `/templates/` | List templates (paginated, filterable by `documento_id`) |
| `GET` | `/templates/{id}` | Get a template by ID |
| `POST` | `/templates/` | Create a template (JSON: `documento_id`, `nome`, `descrizione`) |
| `PATCH` | `/templates/{id}` | Update template name / description |
| `GET` | `/templates/{id}/download` | Download the linked document's file (404 if missing) |
| `DELETE` | `/templates/{id}` | Delete a template record (204; document is preserved) |

### Autenticazione & RBAC

Due piani di autenticazione distinti (vedi [Authentication & access](#authentication--multi-user-access)):

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Login umano: apre una sessione server-side e imposta il cookie `session_token` |
| `POST` | `/auth/logout` | Revoca la sessione corrente e cancella il cookie |
| `POST` | `/auth/token` | Rilascia un JWT a un *service account* (macchina-a-macchina) |
| `GET` | `/auth/me` | Profilo, ruoli e permessi dell'utente autenticato |

Gestione utenti, ruoli e permessi (RBAC):

| Method | Path | Description | Permesso |
|---|---|---|---|
| `GET` | `/utenti/` | Lista utenti (paginata) | `utenti:read` |
| `GET` | `/utenti/{id}` | Dettaglio utente | `utenti:read` |
| `POST` | `/utenti/` | Crea un utente (umano o service account) | `utenti:write` |
| `PATCH` | `/utenti/{id}` | Aggiorna utente (stato, superuser, ruoli) | `utenti:write` |
| `PUT` | `/utenti/{id}/password` | Imposta una nuova password | `utenti:write` |
| `DELETE` | `/utenti/{id}` | Elimina un utente (204) | `utenti:write` |
| `GET` | `/ruoli/` | Lista ruoli (paginata) | `ruoli:read` |
| `GET` | `/ruoli/{id}` | Dettaglio ruolo coi suoi permessi | `ruoli:read` |
| `POST` | `/ruoli/` | Crea un ruolo (409 su nome duplicato) | `ruoli:write` |
| `PATCH` | `/ruoli/{id}` | Aggiorna ruolo / set di permessi | `ruoli:write` |
| `DELETE` | `/ruoli/{id}` | Elimina un ruolo (204) | `ruoli:write` |
| `GET` | `/permessi/` | Catalogo dei permessi disponibili | `ruoli:read` |

I *superuser* bypassano il controllo dei permessi. Gli endpoint di dominio non
sono ancora protetti dalle guardie RBAC: i permessi `anagrafica:*`,
`contabilita:*`, `servizi:*`, `archivio:*` sono già definiti e pronti per essere
applicati.

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
| `DATABASE_URL` | `postgresql+asyncpg://user:password@localhost:5432/associazione_db` | Async PostgreSQL connection string used by the API at runtime (least-privilege role in production) |
| `MIGRATION_DATABASE_URL` | _(unset → falls back to `DATABASE_URL`)_ | Connection string used by Alembic for DDL — the schema-owner role |
| `APP_ENV` | `development` | Environment name — controls log format (JSON in non-development) |
| `APP_DEBUG` | `true` | Enables debug log level |
| `SECRET_KEY` | `changeme` | Application secret key |
| `JWT_SECRET_KEY` | `changeme` | HS256 signing key for service-account JWTs — **must** be overridden in production |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | `10080` (7 days) | Lifetime of a service-account JWT |
| `SESSION_EXPIRE_HOURS` | `12` | Lifetime of a human session |
| `SESSION_COOKIE_NAME` | `session_token` | Name of the session cookie |
| `SESSION_COOKIE_SECURE` | `false` | Mark the session cookie `Secure` (set `true` behind HTTPS) |
| `BOOTSTRAP_ADMIN_PASSWORD` | `changeme` | Password for the seeded `admin@associazione.example` superuser (read by the auth migration) |
| `APP_RW_PASSWORD` | `app_rw` | Password for the `app_rw` DB role (consumed by `db/01-roles.sh`) |
| `APP_RO_PASSWORD` | `app_ro` | Password for the `app_ro` DB role (consumed by `db/01-roles.sh`) |

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

## Authentication & multi-user access

The API separates two distinct authentication planes. Credentials are managed
natively (email + bcrypt password hash) — no external OAuth2 provider.

**Machine-to-machine — JWT**
Service accounts (`tipo = servizio`) for workers, bots, and bulk-import
services obtain a signed HS256 JWT from `POST /auth/token` and present it as
`Authorization: Bearer <jwt>`. Stateless and long-lived.

**Human users — server-side sessions**
Humans (`tipo = umano`) authenticate at `POST /auth/login`; the server opens a
revocable session and returns an opaque token in the `session_token` cookie
(only its SHA-256 hash is stored). `POST /auth/logout` revokes it. Sessions are
revocable and expire after `SESSION_EXPIRE_HOURS`.

**RBAC — association-configurable**
A single `Utente` principal (human or service) carries `Ruolo`s, and each role
grants a set of `Permesso`s (`risorsa:azione`, e.g. `contabilita:read`). The
mapping of permissions to roles is data, not code — each banda can decide which
permissions a direttivo carica (tesoriere, segretario, presidente, …) gets.
`superuser` accounts bypass the permission check entirely.

**Tables:** `utenti`, `ruoli`, `permessi`, `ruoli_permessi`, `utenti_ruoli`,
`sessioni`.

**Bootstrap:** the auth migration seeds the permission catalogue, a global
`superuser` role, and an `admin@associazione.example` superuser whose password
comes from `BOOTSTRAP_ADMIN_PASSWORD` (default `changeme` — change it).

### Database users (least-privilege roles)

Database access is layered separately from the application login:

| Role | Privileges | Used by |
|---|---|---|
| `associazione` (`POSTGRES_USER`) | Owner — full DDL | Alembic migrations (`MIGRATION_DATABASE_URL`) |
| `app_rw` | DML only (SELECT/INSERT/UPDATE/DELETE) | The API at runtime (`DATABASE_URL`) |
| `app_ro` | SELECT only | Reporting / analytics / export workers |

`db/01-roles.sh` runs once at first database init (mounted into
`docker-entrypoint-initdb.d`) to create the roles and grant privileges,
including `ALTER DEFAULT PRIVILEGES` so future migration tables are covered
automatically. Role passwords come from `APP_RW_PASSWORD` / `APP_RO_PASSWORD`.
For an existing database, run the script's SQL manually as the schema owner.

## Roadmap

### Other planned features

- **Dynamic document system** — a field configurator and frontend renderer built
  on top of the `Template` model. Will support receipts (for members and
  externals), annual financial reports populated from contabilità data, and other
  document types. Planned as a separate repository linked to this API.
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
