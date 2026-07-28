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
│       ├── auth.py                        # Login/logout (sessions), JWT issuance, /me, register, password reset
│       ├── oauth.py                       # OAuth2 SSO (Google, Facebook, Apple) redirect + callback
│       ├── utenti.py                      # Users router (humans & service accounts)
│       ├── ruoli.py                       # Roles router (RBAC)
│       ├── permessi.py                    # Permissions catalogue (read-only)
│       ├── persone.py                     # People (anagrafica) router + addresses (M2M)
│       ├── indirizzi.py                   # Addresses router
│       ├── contatti.py                    # Contacts router
│       ├── soci.py                        # Members router
│       ├── esterni.py                     # Externals router
│       ├── iscrizioni.py                  # Annual subscriptions router
│       ├── committenti.py                 # Event clients (committenti) router
│       ├── servizi.py                     # Events router (filterable by year) + libretto PDF generation
│       ├── ricevute.py                    # Receipts router
│       ├── presenze.py                    # Attendance / event roster router
│       ├── repertorio_items.py            # Event programme (repertorio) router
│       ├── voci_contabilita.py            # Accounting items router
│       ├── flussi_cassa.py                # Cash-flow movements router
│       ├── configurazione_banda_anno.py   # Annual band configuration router (year closure)
│       ├── rendiconto.py                  # Accounting statements & exports (PDF/XLSX)
│       ├── check_quote.py                 # Membership quota verification
│       ├── stati.py                       # Lookup routers: states, regions, provinces,
│       ├── regioni.py                     #   municipalities, instruments, address types,
│       ├── province.py                    #   bands, contact/band roles, rendiconto
│       ├── comuni.py                      #   sections/items/sub-items, cash-flow natures,
│       ├── strumenti.py                   #   document types, score types, subscription
│       ├── tipi_indirizzo.py              #   states, band roles, contact roles
│       ├── bande.py                       # Bands router (with address M2M)
│       ├── ruoli_contatto.py              # Contact roles lookup
│       ├── ruoli_banda.py                 # Band roles lookup
│       ├── sezioni_rendiconto.py          # Accounting sections lookup
│       ├── voci_rendiconto.py             # Accounting items lookup
│       ├── sottovoci_rendiconto.py        # Accounting sub-items lookup
│       ├── nature_flusso.py               # Cash-flow natures lookup
│       ├── tipi_documento.py              # Document types lookup
│       ├── tipi_spartito.py               # Score types lookup
│       ├── stati_iscrizione.py            # Subscription states lookup
│       ├── documenti.py                   # Documents router (file repository)
│       ├── macro_sezioni.py               # Archive macro-sections lookup (read-only, seeded)
│       ├── sotto_cartelle.py              # User-managed sub-folders inside a macro-section
│       ├── nome_parti.py                  # Compositions router (score archive, level 1)
│       ├── spartiti.py                    # Scores router (score archive, level 2)
│       ├── templates.py                   # Templates router: CRUD + HTML preview + DOCX/PDF generation
│       └── mergefields.py                 # Catalogue of merge fields available to templates
├── core/
│   ├── config.py        # Settings (pydantic-settings)
│   ├── database.py      # Async engine & session factory
│   ├── logging.py       # Shim → associazione_toolkit.logging
│   ├── middleware.py     # Request ID & timing middleware
│   ├── security.py      # Password hashing, JWT, session tokens
│   └── storage.py       # File upload & validation (local filesystem or Cloudflare R2)
├── exceptions/          # Domain-specific exceptions
├── mergefields/          # Per-entity merge-field providers + registry (dynamic templates)
├── models/              # SQLAlchemy models (lookups.py + entity modules)
├── repositories/        # Data access layer (lookup.py = generic lookup CRUD)
├── schemas/             # Pydantic request/response schemas
├── services/            # Business logic layer (lookup.py = generic lookup CRUD)
│   └── render/           # Template rendering pipeline (HTML, DOCX, PDF via paged.js)
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
**Esterno** — are backed by **dimension (lookup) tables**: geographic (`Stato`, `Regione`,
`Provincia`, `Comune`), organizational (`Banda`, `Strumento`, `TipoIndirizzo`,
`RuoloBanda`, `RuoloContatto`), accounting (`SezioneRendiconto`, `VoceRendiconto`,
`SottovoceRendiconto`, `NaturaFlusso`), and documentary (`TipoDocumento`, `TipoSpartito`,
`StatoIscrizione`). A person can hold several addresses (many-to-many via `persone_indirizzi`);
a band can hold several addresses too (`bande_indirizzi`). Band membership (`banda_codice`)
is held on **Persona** and inherited by **Socio** and **Esterno** through their person —
there is no separate band column on those entities. All 16 lookup tables share a
generic CRUD stack (`repositories/lookup.py`, `services/lookup.py`) to avoid
duplication; the generic list supports optional equality filters (used e.g. by
`/comuni/?provincia_codice=`).

**Iscrizione** models a member's annual subscription: each socio must subscribe
once per year (unique constraint on `socio_id` + `anno`), with a participation
quota, a payment state, and optional references to the membership document and
the receipt issued for the payment.

Events and receipts are modelled by **Servizio** (T_Servizi) and **Ricevuta**
(T_Ricevute). A receipt always refers to a **Persona** — a member or an
external, whoever is being paid (`persona_id`, generalized from the earlier
`esterno_id`-only model so a socio can be paid too) — or to neither
(`servizio_id`/`persona_id` both null, for a member's annual subscription
quota, referenced from `Iscrizione`). `esterno_id` is still present on the
table for backward compatibility with historical rows but is no longer
written by the application; it will be dropped in a future migration once
the `persona_id` backfill is fully validated. A `tipo_ricevuta`
(`PAGAMENTO` / `RISCOSSIONE`) distinguishes a fee paid out from a
collection from a committente; it is nullable because it isn't derivable
with certainty for older rows. A service may optionally reference a
**Committente** — the reusable client entity (parrocchia, comune,
pro-loco, …) that commissioned it; the specific on-site contact for that one
event lives on `Servizio.referente` instead, since it can change even for
repeat clients.

**Presenza** tracks who is called to (and, later, actually attends) a
service: it links a `Persona` to a `Servizio` (unique per pair), with a
nullable `stato` (`PRESENTE` / `ASSENTE` / `GIUSTIFICATO`) — null while the
person is only "in organico" and attendance hasn't been tracked yet.
`servizio_id` is nullable with a `CHECK` requiring it for now, in
anticipation of future arcs (`prova_id`, `lezione_id`) once rehearsals and
lessons are modelled. **RepertorioItem** follows the same exclusive-arc
pattern to build a service's programme: it links a `NomeParte` to a
`Servizio` (unique per pair) with an explicit `ordine` (playing position)
and optional `note`.

The score archive is a two-level model: **NomeParte** is the musical
composition (e.g. "Nessun dorma"), and **Spartito** is one physical/digital
part of it — it links to a `Documento` (the PDF file), a score type
(marcia festiva, inno religioso, …), an optional instrument (null means a
single PDF containing all parts), and optional physical location (scaffale /
ripiano / cartella). A `NomeParte` can have zero `Spartito` rows (a band can
register a piece's existence before archiving its files).

`GET /servizi/{id}/libretto` cross-references `RepertorioItem` (ordered by
`ordine`) against each person in the event's `Presenza` roster: for every
piece it picks the `Spartito` matching that person's instrument (resolved
from `Esterno.strumento_codice`, always set, or `Socio.strumento_codice`,
optional), falling back to the instrument-agnostic `Spartito` if one
exists, and merges the resulting PDFs with `pypdf` into a personalized
booklet. Missing pieces (no matching score, or an instrument that couldn't
be determined) are never silently dropped — they're reported explicitly
(a response header for a single person, a JSON manifest entry for the
whole roster).

**Documento** is a pure file archive — a PDF repository decoupled from the
membership model, classified by `TipoDocumento` and optionally filed under a
**SottoCartella** (a user-created sub-folder inside one of a fixed set of
seeded **MacroSezione** — e.g. "Certificazioni Uniche", "Verbali" — each
carrying its own RBAC permission prefix instead of the generic
`archivio:*`). Other aggregates (Spartito, Iscrizione, Ricevuta, Template)
reference documents by FK.

**Template** is the dynamic-document system: a JSON-defined document body
(`contenuto_json`) plus a list of required entity types (`entita_richieste`,
e.g. `socio`, `servizio`, `ricevuta`), rendered by substituting **merge
fields** resolved at request time from real records (`app/mergefields/` —
one provider per entity: banda, socio, esterno, contatto, servizio,
ricevuta, iscrizione). A template can be previewed as HTML, or generated as
a DOCX (direct XML manipulation) or a PDF (HTML → paged.js pagination →
headless-Chromium capture via Playwright); a PDF/DOCX generation persists
its output as a new `Documento`.

Accounting (contabilità) is modelled by **VoceContabilita** (S_VoceContabilita —
a band's chart-of-accounts line, classified by rendiconto section/item/sub-item)
and **FlussoCassa** (T_FlussoCassa — cash movements against an accounting item,
with a sign and a cash/bank nature). Every movement carries a `tipo`
(`MOVIMENTO`, `SALDO_INIZIALE`, `TRASFERIMENTO_USCITA`, `TRASFERIMENTO_ENTRATA`,
`AUTO_ISCRIZIONE`), an optional `iscrizione_id` FK (for auto-generated movements
from a paid subscription), and an optional `trasferimento_id` UUID (a shared
group key linking the two legs of a cassa↔banca transfer).

**ConfigurazioneBandaAnno** holds the annual configuration for a band:
opening balances, the expected membership quota, and a reference to the
"quote associative" accounting item. Once the year is **closed**
(`chiuso = True`), all mutations on `FlussoCassa` rows belonging to that
(banda, anno) pair are blocked with `409`. The year is re-openable by a
superuser via `POST /{id}/riapri`.

## API endpoints

Base prefix: `/api/v1`

### Persone (anagrafica)

| Method | Path | Description |
|---|---|---|
| `GET` | `/persone/` | List people (paginated, filterable by `banda_codice`) |
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
| `GET` | `/soci/?banda_codice={codice}` | Members of a band (paginated) |
| `GET` | `/esterni/?banda_codice={codice}` | Externals of a band (paginated) |
| `GET` | `/contatti/persona/{persona_id}` | Contacts for a person (paginated) |
| `GET` | `/iscrizioni/?socio_id={id}` | Subscriptions for a member (paginated) |
| `GET` | `/iscrizioni/?anno={anno}` | Subscriptions for a given year (paginated) |

`Socio` and `Esterno` require an existing `persona_id` (404 otherwise) and reject
duplicate codes (409). Band membership lives on `Persona` (`banda_codice`): soci
and esterni inherit it through their person, so the `banda_codice` filter joins
`Persona`, and a member's code is unique *within its band*. `Contatto` requires an
existing `persona_id`. `Iscrizione` requires an existing `socio_id` (404) and
rejects duplicate `(socio_id, anno)` pairs (409 — one subscription per member per
year).

`IndirizzoResponse` embeds a nested `comune` object (`{ codice, descrizione }`)
eager-loaded via `selectinload`, so callers receive the city name without an extra
lookup. This applies to all indirizzo endpoints and to the person's address list
(`GET /persone/{id}/indirizzi`).

### Committenti

Standard CRUD under `/committenti`: `GET /` (paginated), `GET /{id}`, `POST /`,
`PATCH /{id}`, `DELETE /{id}` (204; 409 if still referenced by a `Servizio`).
`Committente.indirizzo_id`, if provided, must reference an existing `Indirizzo`
(404 otherwise).

### Servizi · Ricevute (events & receipts)

Standard CRUD under `/servizi` and `/ricevute`. In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/servizi/?anno={anno}&banda_codice={codice}` | List events, filterable by year and/or band (paginated) |
| `GET` | `/servizi/{servizio_id}/libretto?persona_id={id}` | Generate the concert booklet PDF (see below) |
| `GET` | `/ricevute/servizio/{servizio_id}` | Receipts for an event (paginated) |

`Servizio` requires an existing `indirizzo_id` (404), and cannot be deleted while
it has receipts (409). Its optional `committente_id` is validated if provided
(404). `Ricevuta` supports two use cases: a fee/collection tied to a person
(`servizio_id` + `persona_id`, both validated if provided; the person can be a
member or an external) and a member's subscription receipt (both omitted,
referenced from `Iscrizione`). Receipt responses embed the related `persona`,
eager-loaded to avoid N+1 queries.

**`GET /servizi/{servizio_id}/libretto`** merges, for each person in the
event's roster (`Presenza`), the scores matching their instrument across the
whole programme (`RepertorioItem`, in `ordine`) into one PDF:

- `?persona_id=` generates a single person's booklet: `Response` with
  `media_type=application/pdf`; missing pieces (if any) are listed in the
  `X-Brani-Mancanti` header. `404` if that person has literally no score for
  any piece in the programme (an empty booklet isn't a valid download), if
  the person isn't in the roster, or if the event has no roster/programme at
  all.
- without `persona_id`, generates the whole roster at once: a ZIP
  (`application/zip`) with one PDF per person plus a `report.json` listing,
  per person, missing pieces or a note that no score was found at all for
  them — a person with an entirely empty booklet doesn't block the ZIP for
  everyone else, they just get no PDF entry and an explicit `errore` in the
  report instead.

### Presenze (event roster & attendance)

| Method | Path | Description |
|---|---|---|
| `GET` | `/presenze/servizio/{servizio_id}` | Roster/attendance for an event (paginated) |
| `GET` | `/presenze/{id}` | Get a roster entry by ID |
| `POST` | `/presenze/` | Add a person to an event's roster (`persona_id` + `servizio_id`) |
| `PATCH` | `/presenze/{id}` | Update `stato` (`PRESENTE`/`ASSENTE`/`GIUSTIFICATO`) and/or `note` |
| `DELETE` | `/presenze/{id}` | Remove a roster entry (204) |

Requires existing `persona_id` and `servizio_id` (404 otherwise); rejects a
person appearing twice on the same event's roster (409).

### Repertorio (event programme)

| Method | Path | Description |
|---|---|---|
| `GET` | `/repertorio/servizio/{servizio_id}` | Programme for an event, ordered by `ordine` (paginated) |
| `GET` | `/repertorio/{id}` | Get a programme entry by ID |
| `POST` | `/repertorio/` | Add a piece to an event's programme (`nome_parte_id` + `servizio_id` + `ordine`) |
| `PATCH` | `/repertorio/{id}` | Update `ordine` and/or `note` |
| `DELETE` | `/repertorio/{id}` | Remove a programme entry (204) |

Requires existing `nome_parte_id` and `servizio_id` (404 otherwise); rejects the
same piece appearing twice in the same event's programme (409). `ordine` is not
DB-unique per event — reordering the programme is expected to be a common
operation, and enforcing uniqueness would force multi-step shuffles to avoid
transient conflicts, for a constraint the application layer can keep sane
either way.

### NomeParti · Spartiti (score archive)

Two-level archive: `NomeParte` is the composition, `Spartito` is one of its
parts. Standard CRUD under `/nome-parti` and `/spartiti`. In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/nome-parti/?banda_codice={codice}` | List compositions, filterable by `tipo_spartito_codice` / `nome` (paginated) |
| `POST` | `/nome-parti/{id}/audio` | Attach a reference audio file (upload) |
| `DELETE` | `/nome-parti/{id}/audio` | Detach the reference audio file (204) |

### Contabilità (accounting)

Standard CRUD under `/voci-contabilita` and `/flussi-cassa`. In addition:

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/voci-contabilita/?banda_codice={codice}` | Accounting items, filterable by band | — |
| `GET` | `/flussi-cassa/` | List cash movements (paginated) | — |
| `GET` | `/flussi-cassa/{flusso_id}` | Get a cash movement | — |
| `GET` | `/flussi-cassa/voce-contabilita/{voce_id}` | Cash movements for an accounting item (paginated) | — |
| `POST` | `/flussi-cassa/` | Create a cash movement | — |
| `PATCH` | `/flussi-cassa/{flusso_id}` | Update a cash movement | — |
| `DELETE` | `/flussi-cassa/{flusso_id}` | Delete a cash movement (204) | — |
| `POST` | `/flussi-cassa/trasferimenti/` | Create a bank transfer (pair of movements) | `contabilita:write` |
| `GET` | `/contabilita/check-quote/?banda_codice={b}&anno={a}` | Verify quota balances | `contabilita:read` |
| `GET` | `/contabilita/rendiconto/?banda_codice={b}&anno={a}` | Get accounting statement | `contabilita:read` |
| `GET` | `/contabilita/rendiconto/mensile?banda_codice={b}&anno={a}` | Get monthly breakdown | `contabilita:read` |
| `GET` | `/contabilita/rendiconto/export/pdf?banda_codice={b}&anno={a}` | Export statement as PDF | `contabilita:read` |
| `GET` | `/contabilita/rendiconto/export/xlsx?banda_codice={b}&anno={a}` | Export statement as Excel | `contabilita:read` |

A `VoceContabilita` cannot be deleted while it has cash movements (409). A
`FlussoCassa` requires an existing `voce_contabilita_id` (404 otherwise).

**Year-closure enforcement:** create, update, and delete on `FlussoCassa` are
blocked with `409 Conflict` if the movement's `(banda, anno)` pair — derived
from `voce_contabilita.banda_codice` and `data_registrazione.year` — is closed
(`ConfigurazioneBandaAnno.chiuso = True`). For updates that change the year via
`data_registrazione`, the destination year is also checked.

**Trasferimenti (bank transfers):** the POST `/flussi-cassa/trasferimenti/` endpoint
creates a pair of balanced cash movements representing a transfer between accounts
(e.g. cassa ↔ banca), sharing a `trasferimento_id` UUID to link them.

#### Configurazione banda/anno

Standard CRUD under `/configurazioni-banda-anno`. In addition:

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/configurazioni-banda-anno/?banda_codice={b}&anno={a}` | List, filterable by band and/or year | `contabilita:read` |
| `GET` | `/configurazioni-banda-anno/banda/{b}/anno/{a}` | Get by (banda, anno) | `contabilita:read` |
| `POST` | `/configurazioni-banda-anno/{id}/chiudi` | Close the year — sets `chiuso=True`, records timestamp and acting user. 409 if already closed. | `contabilita:write` |
| `POST` | `/configurazioni-banda-anno/{id}/riapri` | Reopen the year — clears closure fields. 409 if already open. | superuser only |

Creating the first `ConfigurazioneBandaAnno` for a band automatically seeds 4
minimum `VoceContabilita` rows (Quote associative, Saldo iniziale, Versamento in
banca, Spese bancarie).

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

The geographic lookups accept a hierarchy filter on their list endpoint:
`GET /regioni/?stato_codice=`, `GET /province/?regione_codice=`, and
`GET /comuni/?provincia_codice=` each restrict results to the parent entity
(e.g. `/comuni/?provincia_codice=64`).

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
| `GET` | `/documenti/` | List documents (paginated, filterable by `tipo_documento_codice`, `sotto_cartella_id`) |
| `GET` | `/documenti/{id}` | Get a document by ID |
| `POST` | `/documenti/?tipo_documento_codice={codice}&sotto_cartella_id={id}&note={note}` | Upload a document (any file type; optional `note`) |
| `GET` | `/documenti/{id}/download` | Download a document as attachment (404 if file missing) |
| `GET` | `/documenti/{id}/preview` | Preview a document inline (404 if file missing) |
| `DELETE` | `/documenti/{id}` | Delete a document and its file (204) |

### Macro-sezioni · Sotto-cartelle (archive folders)

The archive is organized in two tiers: a fixed, seeded set of **macro-sezioni**
(e.g. "Certificazioni Uniche", "Verbali") — each with its own RBAC permission
prefix instead of the generic `archivio:*` — containing user-managed
**sotto-cartelle** that documents can be filed under.

| Method | Path | Description |
|---|---|---|
| `GET` | `/macro-sezioni/` | List the macro-section catalogue (read-only, seeded) |
| `GET` | `/sotto-cartelle/?macro_sezione_codice={codice}` | List sub-folders in a macro-section |
| `POST` | `/sotto-cartelle/` | Create a sub-folder (`nome` + `macro_sezione_codice`; 404 if unknown, 409 on duplicate name) |
| `PATCH` | `/sotto-cartelle/{id}` | Rename a sub-folder |
| `DELETE` | `/sotto-cartelle/{id}` | Delete a sub-folder (204) |

### Spartiti

Archives musical scores. Each spartito links to a `Documento` (the PDF), a score
type, and optionally an instrument (`strumento_codice` null = single PDF with all
parts) and physical location.

| Method | Path | Description |
|---|---|---|
| `GET` | `/spartiti/` | List scores (paginated, filterable by `tipo_spartito_codice` / `strumento_codice` / `banda_codice`) |
| `GET` | `/spartiti/{id}` | Get a score by ID |
| `POST` | `/spartiti/` | Create a score record |
| `PATCH` | `/spartiti/{id}` | Update score metadata |
| `DELETE` | `/spartiti/{id}` | Delete a score record (204) |

### Templates (dynamic document rendering)

A `Template` holds a JSON document body (`contenuto_json`) and a list of
required entity types (`entita_richieste`); rendering resolves **merge
fields** from real records and substitutes them into the body, producing
HTML, DOCX, or a paginated PDF.

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/templates/` | List templates (paginated) | `templates:read` |
| `GET` | `/templates/{id}` | Get a template by ID | `templates:read` |
| `POST` | `/templates/` | Create a template (`nome`, `contenuto_json`, `entita_richieste`, optional `sotto_cartella_id`) | `templates:write` |
| `PATCH` | `/templates/{id}` | Update a template | `templates:write` |
| `DELETE` | `/templates/{id}` | Delete a template record (204) | `templates:write` |
| `POST` | `/templates/{id}/preview` | Render `contenuto_json` against the given `entities` (`{entity_name: id}`) and return HTML | `templates:read` |
| `POST` | `/templates/{id}/generate/docx` | Render the template and persist the result as a new `Documento` (.docx) | `templates:read` |
| `POST` | `/templates/{id}/generate/pdf` | Render the template and persist the result as a new `Documento` (.pdf, via paged.js + headless Chromium) | `templates:read` |

`generate/*` accepts `entities` (`{entity_name: id}`) and an optional
`nome_file`; without it, the filename is derived from the template name, the
resolved socio/esterno identity if present, and a timestamp. `404` if the
template or a referenced entity doesn't exist; `400` for an entity name not
covered by any merge-field provider; `422` if rendering itself fails.

### Mergefields

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/mergefields/` | Catalogue of merge fields available per entity (`{chiave, etichetta, tipo}`), for building the template editor UI | `templates:read` |

Each entity (`banda`, `socio`, `esterno`, `contatto`, `servizio`, `ricevuta`,
`iscrizione`) has a dedicated provider under `app/mergefields/providers/`
declaring its available fields and how to resolve them from the DB; adding a
new entity to the template system means adding one provider.

### Autenticazione & RBAC

Due piani di autenticazione distinti (vedi [Authentication & access](#authentication--multi-user-access)):

| Method | Path | Description |
|---|---|---|
| `POST` | `/auth/login` | Login umano: apre una sessione server-side e imposta il cookie `session_token` |
| `POST` | `/auth/logout` | Revoca la sessione corrente e cancella il cookie |
| `POST` | `/auth/token` | Rilascia un JWT a un *service account* (macchina-a-macchina) |
| `GET` | `/auth/me` | Profilo, ruoli e permessi dell'utente autenticato |
| `POST` | `/auth/register` | Auto-registrazione (email + password); assegna il ruolo globale `Ospite` (sola lettura, no contabilità/admin). 409 su email duplicata |
| `POST` | `/auth/password-reset/request` | Richiede l'invio di un'email di reset password. Risponde sempre 200, anche se l'email non è registrata, per non rivelarne l'esistenza |
| `POST` | `/auth/password-reset/confirm` | Consuma un token di reset (`token` + `new_password`); 400 se non valido o scaduto |
| `GET` | `/auth/oauth/{provider}` | Avvia il flusso OAuth2 (`google`, `facebook`, `apple`): redirect 302 al provider |
| `GET`/`POST` | `/auth/oauth/{provider}/callback` | Callback del provider: crea/collega l'utente e apre una sessione (cookie), poi redirect al frontend |

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

#### Catalogo permessi disponibili

Il sistema RBAC include i seguenti permessi atomici nella forma `risorsa:azione`:

| Permesso | Descrizione |
|---|---|
| `utenti:read` | Visualizzare utenti |
| `utenti:write` | Gestire utenti |
| `ruoli:read` | Visualizzare ruoli e permessi |
| `ruoli:write` | Gestire ruoli e permessi |
| `anagrafica:read` | Visualizzare anagrafica (persone, soci, esterni) |
| `anagrafica:write` | Gestire anagrafica |
| `iscrizioni:read` | Visualizzare iscrizioni |
| `iscrizioni:write` | Gestire iscrizioni |
| `contabilita:read` | Visualizzare contabilità |
| `contabilita:write` | Gestire contabilità |
| `servizi:read` | Visualizzare eventi e ricevute |
| `servizi:write` | Gestire eventi e ricevute |
| `archivio:read` | Visualizzare archivio documentale e spartiti |
| `archivio:write` | Gestire archivio documentale e spartiti |
| `templates:read` | Visualizzare, previeware e generare documenti dai template |
| `templates:write` | Gestire template (creazione, modifica, eliminazione) |

Ogni **macro-sezione** dell'archivio (`/macro-sezioni`) porta inoltre un
proprio prefisso di permesso dedicato (es. `certificazioni:read/write`),
seedato via migrazione insieme alla macro-sezione stessa, in alternativa al
generico `archivio:*`.

**Permission enforcement status:**

Currently enforced with `@require_permission()` guards:
- `utenti:*` on all utenti endpoints
- `ruoli:*` on all ruoli endpoints
- `contabilita:*` on contabilità endpoints (`/voci-contabilita`, `/flussi-cassa/trasferimenti`, `/contabilita/rendiconto*`, `/contabilita/check-quote`, `/configurazioni-banda-anno`)
- `templates:*` on `/templates` (all actions) and `/mergefields`
- `ruoli:read` on permessi catalogue

Defined but not yet enforced per-endpoint: `anagrafica:*`, `iscrizioni:*`, `servizi:*`, `archivio:*`.
All domain endpoints still **require authentication** (`Depends(get_current_user)`): without a valid session or JWT, responses are `401`. The `Ospite` role seeded for self-registration (`POST /auth/register`) is granted read-only permissions across the board, excluding `contabilita:*` and admin (`utenti:*`/`ruoli:*`).

*Superuser* accounts bypass all permission checks.

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
| `SESSION_COOKIE_SECURE` | `true` | Mark the session cookie `Secure` (must be `true` behind HTTPS) |
| `SESSION_COOKIE_SAMESITE` | `lax` | `SameSite` attribute of the session cookie (`lax`/`strict`/`none`) |
| `SESSION_COOKIE_DOMAIN` | _(unset)_ | Cookie domain, needed to share the session across subdomains (e.g. `.cosequences.com`) |
| `BOOTSTRAP_ADMIN_PASSWORD` | `changeme` | Password for the seeded `admin@cosequences.com` superuser (read by the auth migration) |
| `APP_RW_PASSWORD` | `app_rw` | Password for the `app_rw` DB role (consumed by `db/01-roles.sh`) |
| `APP_RO_PASSWORD` | `app_ro` | Password for the `app_ro` DB role (consumed by `db/01-roles.sh`) |
| `STORAGE_BACKEND` | `local` | File storage backend: `local` (filesystem under `uploads/`) or `r2` (Cloudflare R2, S3-compatible) |
| `R2_ENDPOINT_URL` / `R2_ACCESS_KEY_ID` / `R2_SECRET_ACCESS_KEY` / `R2_BUCKET_NAME` | _(unset)_ | Required when `STORAGE_BACKEND=r2` |
| `RESEND_API_KEY` | _(unset)_ | [Resend](https://resend.com) API key for transactional email (password reset); if unset, email sending is a no-op |
| `EMAIL_FROM` | `noreply@cosequences.com` | From address for transactional email |
| `FRONTEND_URL` | `https://bandapp.cosequences.com` | Frontend base URL — where OAuth callbacks redirect after login |
| `API_BASE_URL` | `http://localhost:8000` | This API's own base URL — used to build the OAuth2 `redirect_uri` |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | _(unset)_ | Google SSO credentials; `/auth/oauth/google` returns `503` if unset |
| `FACEBOOK_CLIENT_ID` / `FACEBOOK_CLIENT_SECRET` | _(unset)_ | Facebook SSO credentials; `/auth/oauth/facebook` returns `503` if unset |
| `APPLE_CLIENT_ID` / `APPLE_TEAM_ID` / `APPLE_KEY_ID` / `APPLE_PRIVATE_KEY` | _(unset)_ | Apple "Sign in with Apple" credentials; `/auth/oauth/apple` returns `503` if unset |

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
natively (email + bcrypt password hash), with optional OAuth2 SSO as an
alternative human login path.

**Machine-to-machine — JWT**
Service accounts (`tipo = servizio`) for workers, bots, and bulk-import
services obtain a signed HS256 JWT from `POST /auth/token` and present it as
`Authorization: Bearer <jwt>`. Stateless and long-lived.

**Human users — server-side sessions**
Humans (`tipo = umano`) authenticate at `POST /auth/login`; the server opens a
revocable session and returns an opaque token in the `session_token` cookie
(only its SHA-256 hash is stored). `POST /auth/logout` revokes it. Sessions are
revocable and expire after `SESSION_EXPIRE_HOURS`. Humans can also self-register
(`POST /auth/register`, granted the read-only `Ospite` role) and reset a
forgotten password via a one-time emailed token (`POST /auth/password-reset/request`
+ `/confirm`, sent through Resend if `RESEND_API_KEY` is configured).

**Human users — OAuth2 SSO**
`GET /auth/oauth/{google,facebook,apple}` redirects to the provider; on
callback the API creates or links an `OAuthAccount` to a `Utente` and opens the
same kind of server-side session as `/auth/login`, then redirects to
`FRONTEND_URL`. Each provider is optional and returns `503` until its client
ID/secret are configured. The `id_token`/claims are currently decoded without
signature verification (see [Roadmap](#other-planned-features)).

**RBAC — association-configurable**
A single `Utente` principal (human or service) carries `Ruolo`s, and each role
grants a set of `Permesso`s (`risorsa:azione`, e.g. `contabilita:read`). The
mapping of permissions to roles is data, not code — each banda can decide which
permissions a direttivo carica (tesoriere, segretario, presidente, …) gets.
`superuser` accounts bypass the permission check entirely.

**Tables:** `utenti`, `ruoli`, `permessi`, `ruoli_permessi`, `utenti_ruoli`,
`sessioni`, `oauth_accounts`, `password_reset_tokens`.

**Bootstrap:** the auth migration seeds the permission catalogue, a global
`superuser` role, and an `admin@cosequences.com` superuser whose password
comes from `BOOTSTRAP_ADMIN_PASSWORD` (default `changeme` — change it). A later
migration adds the global read-only `Ospite` role used by self-registration.

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

- New document types beyond the existing merge-field providers (banda, socio,
  esterno, contatto, servizio, ricevuta, iscrizione) — e.g. annual financial
  reports populated from contabilità data, assembly minutes. Mostly need a new
  provider plus a template body, not new backend plumbing.
- Bulk import of members and externals from Excel files (via async worker)
- Auto-posting of service-related receipts (compensi/riscossioni) to
  `FlussoCassa`, on the pattern already used for `AUTO_ISCRIZIONE` — needs a
  new accounting-item configuration primitive (the existing
  `ConfigurazioneBandaAnno.voce_contabilita_quote_id` only covers membership
  quotes) plus a rule for which `natura_flusso`/sign to use; deliberately left
  out of the `Ricevuta.persona_id` generalization pending that design.
- OAuth `id_token` signature verification (currently decoded without
  signature check — acceptable short-term since the token arrives directly
  from the provider over HTTPS in the same request, but should be hardened
  before wider production reliance)
- Telegram / email notification service (beyond the password-reset email)

## Related repositories

| Repository | Description |
|---|---|
| [associazione-api-toolkit](https://github.com/DevilFlow92/associazione-api-toolkit) | Shared utilities — logging, pagination, retry, HTTP client |
| [associazione-api-infra](https://github.com/DevilFlow92/associazione-api-infra) | Infrastructure — Helm charts + Kustomize for Kubernetes |
| **associazione-api** | ← you are here |
