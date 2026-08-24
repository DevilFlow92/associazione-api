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
│       ├── prove.py                       # Rehearsals router (standalone or event-oriented) + libretto PDF generation
│       ├── ricevute.py                    # Receipts router
│       ├── presenze.py                    # Attendance / event-rehearsal-lesson roster router
│       ├── repertorio_items.py            # Event/rehearsal programme (repertorio) router
│       ├── corsi.py                       # Music courses router
│       ├── allievi.py                     # Students (anagrafica, non-socio/esterno) router
│       ├── lezioni.py                     # Course lesson calendar router
│       ├── iscrizioni_corso.py            # Course enrolments router
│       ├── pagamenti_corso.py             # Course fee payments router (auto-posts to FlussoCassa)
│       ├── categorie_voce_programma.py    # Programme item categories lookup
│       ├── catalogo_programmi.py          # Reusable programme catalogue (scale, tecnica, repertorio, ...)
│       ├── schede_alunno.py               # Student record router (row-level authorization) +
│       │                                  #   voci di programma, materiale didattico, autovalutazioni,
│       │                                  #   storico dei cambi di stato (sola lettura)
│       ├── portale_alunno.py              # Student self-service portal (/me/...)
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
│       ├── tipi_indirizzo.py              #   states, band roles, contact roles,
│       │                                  #   course types, course enrolment states
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
│       ├── tipi_corso.py                  # Course types lookup
│       ├── stati_iscrizione_corso.py      # Course enrolment states lookup
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
`StatoIscrizione`, `TipoCorso`). A person can hold several addresses (many-to-many via `persone_indirizzi`);
a band can hold several addresses too (`bande_indirizzi`). Band membership (`banda_codice`)
is held on **Persona** and inherited by **Socio** and **Esterno** through their person —
there is no separate band column on those entities. All 17 lookup tables share a
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

**Prova** models a rehearsal: `banda_codice`, a single `data_prova`
datetime, an optional `indirizzo_id` (unlike `Servizio.indirizzo_id`, it's
nullable — a rehearsal can be called quickly before a venue is settled),
and an optional `servizio_id` — set when the rehearsal is in preparation
for a specific event, null for a standalone rehearsal (e.g. rehearsing a
freshly renewed march repertoire).

**Lezione** models a single dated session of a **Corso**: `corso_id` is
required (unlike `Prova`, a lesson always belongs to a course, never
standalone), plus `data_lezione` and an optional `indirizzo_id`.

**Presenza** tracks who is called to (and, later, actually attends) a
service, rehearsal, or lesson: it links a `Persona` to exactly one of
`Servizio`, `Prova`, or `Lezione` — a three-branch exclusive arc enforced
by both a DB `CHECK` (enumerating the three valid combinations of
nullable/non-null columns) and a Pydantic validator — with a nullable
`stato` (`PRESENTE` / `ASSENTE` / `GIUSTIFICATO`), null while the person is
only "in organico" and attendance hasn't been tracked yet, and unique per
`(persona_id, servizio_id | prova_id | lezione_id)`. **RepertorioItem**
follows the same two-branch exclusive-arc pattern (`Servizio`/`Prova` only
— a lesson has no repertoire) to build a programme: it links a `NomeParte`
to a `Servizio`/`Prova` (unique per pair) with an explicit `ordine`
(playing position) and optional `note`.

`GET /prove/{id}/libretto` mirrors `GET /servizi/{id}/libretto` exactly
(same merge/fallback/missing-piece-report logic, reusing `LibrettoService`
with `prova_id` instead of `servizio_id`).

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
`archivio:*`). Other aggregates (Spartito, Iscrizione, IscrizioneCorso,
Ricevuta, Template) reference documents by FK.

**Template** is the dynamic-document system: a JSON-defined document body
(`contenuto_json`) plus a list of required entity types (`entita_richieste`,
e.g. `socio`, `servizio`, `ricevuta`), rendered by substituting **merge
fields** resolved at request time from real records (`app/mergefields/` —
one provider per entity: banda, socio, esterno, contatto, servizio,
ricevuta, iscrizione, allievo, iscrizione_corso). A template can be previewed as HTML, or generated as
a DOCX (direct XML manipulation) or a PDF (HTML → paged.js pagination →
headless-Chromium capture via Playwright); a PDF/DOCX generation persists
its output as a new `Documento`.

Accounting (contabilità) is modelled by **VoceContabilita** (S_VoceContabilita —
a band's chart-of-accounts line, classified by rendiconto section/item/sub-item)
and **FlussoCassa** (T_FlussoCassa — cash movements against an accounting item,
with a sign and a cash/bank nature). Every movement carries a `tipo`
(`MOVIMENTO`, `SALDO_INIZIALE`, `TRASFERIMENTO_USCITA`, `TRASFERIMENTO_ENTRATA`,
`AUTO_ISCRIZIONE`, `AUTO_PAGAMENTO_CORSO`), an optional `iscrizione_id` FK
(for auto-generated movements from a paid subscription), and an optional
`trasferimento_id` UUID (a shared group key linking the two legs of a
cassa↔banca transfer).

**ConfigurazioneBandaAnno** holds the annual configuration for a band:
opening balances, the expected membership quota, a reference to the
"quote associative" accounting item (`voce_contabilita_quote_id`), and a
separate reference to the "corsi musicali" accounting item
(`voce_contabilita_corsi_id`, used by `PagamentoCorso` auto-posting — see
below). Once the year is **closed** (`chiuso = True`), all mutations on
`FlussoCassa` rows belonging to that (banda, anno) pair are blocked with
`409`. The year is re-openable by a superuser via `POST /{id}/riapri`.

**Corso** models a band's music course for a given year (e.g. brass,
percussion, woodwind, piano — classified by the **TipoCorso** lookup), with
an optional **coordinatore** and **insegnante**. Both reference `Persona`
directly (`coordinatore_persona_id`/`insegnante_persona_id`), not `Socio` —
the same generalization already used by `Ricevuta.persona_id`, since a
teacher can be an external hire rather than a member. No uniqueness
constraint is enforced on `(tipo_corso_codice, anno, banda_codice)`: running
several parallel courses of the same type in the same year (different
levels, different teachers) is a legitimate case in this domain.

**Allievo** is a dedicated anagrafica entity for course students who are
neither a `Socio` nor an `Esterno`: it links a `Persona` (`persona_id`,
unique — a person holds at most one `Allievo` record) with a
`codice_allievo` and an optional `indirizzo_id`, following the same
`Persona`-first pattern as `Socio`/`Esterno`; `banda_codice` is not a
column on `Allievo` itself, it's inherited from `Persona` and used to
filter (`GET /allievi/?banda_codice=`), same as soci/esterni.

**IscrizioneCorso** models a `Persona`'s enrolment to a `Corso` — distinct
from `Iscrizione` (a `Socio`'s annual membership subscription): the
enrollee here is any `Persona`, not necessarily a member, since a newcomer
can enrol in a course before ever becoming a socio. It carries a
`stato_iscrizione_corso_codice` (**StatoIscrizioneCorso** lookup), an
optional `documento_id`, and `data_iscrizione`. No uniqueness constraint on
`(persona_id, corso_id)`: a person can be re-enrolled after a cancelled
enrolment.

**PagamentoCorso** records a course-fee payment against an
`IscrizioneCorso`. Creating one **auto-posts**, on the same pattern as
`Iscrizione`/`AUTO_ISCRIZIONE`: a `Ricevuta` (`RISCOSSIONE`) and a
`FlussoCassa` (`AUTO_PAGAMENTO_CORSO`, natura Banca) are generated
automatically against `ConfigurazioneBandaAnno.voce_contabilita_corsi_id`
for the enrolment's (banda, anno) — `422` if that configuration is missing.
`ricevuta_id` is nullable for symmetry with `Iscrizione.ricevuta_id` but is
always set by the service in practice.

**VoceProgrammaCatalogo** is a reusable catalogue of programme items (scales,
technique, repertoire, …), classified by `TipoCorso` and **CategoriaVoceProgramma**
(a plain lookup) with a `livello` and free `testo`. "Deleting" one from the
catalogue is a soft-delete (`attiva = False`, via `PATCH`) — never a hard
`DELETE` — so historical references from already-compiled student records are
never invalidated. **SchedaAlunnoVoce** picks one catalogue item into a specific
student's programme, specialized with `stato` (`da_iniziare` / `in_corso` /
`acquisita`), free `dettaglio`, and an explicit `ordine` (teaching sequence, not
alphabetical or insertion order); the same catalogue item can appear more than
once on the same record with a different `dettaglio`. Every creation and every
`stato` change is appended to **SchedaAlunnoVoceStorico**, an append-only log —
never updated, never deleted, except that `scheda_alunno_voce_id` is cleared
(not the row itself) when the voce is removed. `scheda_alunno_id` and
`voce_catalogo_id` on the storico row are deliberately denormalized plain
integers, not FKs: the row must stay queryable and consultable even after its
voce (or, in principle, its catalogue item) is gone, which a FK reference
could not survive. The read surface (`GET .../storico-voci`) enriches each row
with the catalogue text via a separate lookup, keyed by that denormalized id,
falling back to `null` instead of failing when the catalogue item is no
longer resolvable.

**SchedaAlunnoMateriale** attaches teaching material to a student record:
either an uploaded file (validated extension whitelist, 20 MB limit) or an
external link, never both — a two-branch exclusive arc, same pattern as
`Presenza`. Unlike the voci, there's no history to preserve here: deletion is
a hard delete that also removes the underlying storage object for file
materials, leaving no orphan.

**SchedaAlunnoAutovalutazione** is a free-text self-assessment diary written
by the student themselves about their own record — not a teacher's
judgement. It is the first (and so far only) case in the project where the
student *writes*, not just reads, a row of their own record: see
[Schede alunno](#schede-alunno-row-level-authorization) below for how its
authorization perimeter deliberately diverges from the rest of the record.

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

### Prove (rehearsals)

Standard CRUD under `/prove` (`servizi:read`/`servizi:write` — same
permission group as `Servizio`, not `corsi:*`). In addition:

| Method | Path | Description |
|---|---|---|
| `GET` | `/prove/?banda_codice={b}&servizio_id={s}` | List rehearsals, filterable by band and/or the event they prepare (paginated) |
| `GET` | `/prove/{prova_id}/libretto?persona_id={id}` | Generate the rehearsal booklet PDF — identical logic to `/servizi/{id}/libretto`, reusing the same roster (`Presenza`) and programme (`RepertorioItem`) with `prova_id` |

`Prova` requires an existing `servizio_id` if provided (404); `indirizzo_id`
is optional and, unlike `Servizio`, may be left unset while the venue is
still being decided.

### Presenze (event/rehearsal/lesson roster & attendance)

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/presenze/servizio/{servizio_id}` | Roster/attendance for an event (paginated) | `servizi:read` |
| `GET` | `/presenze/prova/{prova_id}` | Roster/attendance for a rehearsal (paginated) | `servizi:read` |
| `GET` | `/presenze/lezione/{lezione_id}` | Roster/attendance for a lesson (paginated) | `corsi:read` |
| `GET` | `/presenze/{id}` | Get a roster entry by ID | `servizi:read` |
| `POST` | `/presenze/` | Add a person to a roster (`persona_id` + exactly one of `servizio_id`/`prova_id`/`lezione_id`) | `servizi:write` or `corsi:write`, chosen from the container in the payload |
| `PATCH`/`DELETE` | `/presenze/{id}` | Update `stato`/`note`, or remove (204) | `servizi:write` or `corsi:write`, chosen from the existing row's container |
| `PATCH` | `/presenze/bulk` | Bulk-update `stato`/`note` for several entries at once | `servizi:write` |

Requires an existing `persona_id` and exactly one of `servizio_id` /
`prova_id` / `lezione_id` (404/422 otherwise, enforced by both a DB `CHECK`
and a Pydantic validator); rejects a person appearing twice on the same
roster (409). The `servizio`/`prova` endpoints are gated by `servizi:*`
uniformly; the `lezione` endpoint and the write path when the payload/row
targets a lesson are gated by `corsi:*` instead, so a future
teacher-only role (`corsi:*` without `servizi:*`) isn't locked out of their
own lesson rosters. On `PATCH`/`DELETE`, the permission check happens
*after* loading the existing row (to know its container) but *before* the
mutation — an unauthorized caller on an existing row gets `403`, not `404`
(a minor, accepted information leak: the permission isn't otherwise
derivable without loading the row). `PATCH /presenze/bulk` and
`GET /presenze/{id}` are not yet split this way and remain under
`servizi:*` regardless of container — a known residual gap, not yet hit in
practice because lesson rosters are managed through
`GET /presenze/lezione/{id}` + per-row `PATCH`.

### Repertorio (event/rehearsal programme)

| Method | Path | Description |
|---|---|---|
| `GET` | `/repertorio/servizio/{servizio_id}` | Programme for an event, ordered by `ordine` (paginated) |
| `GET` | `/repertorio/prova/{prova_id}` | Programme for a rehearsal, ordered by `ordine` (paginated) |
| `GET` | `/repertorio/{id}` | Get a programme entry by ID |
| `POST` | `/repertorio/` | Add a piece to a programme (`nome_parte_id` + exactly one of `servizio_id`/`prova_id` + `ordine`) |
| `PATCH` | `/repertorio/{id}` | Update `ordine` and/or `note` |
| `DELETE` | `/repertorio/{id}` | Remove a programme entry (204) |

Gated uniformly by `servizi:read`/`servizi:write`, for both the `servizio`
and `prova` branches. Requires an existing `nome_parte_id` and exactly one
of `servizio_id`/`prova_id` (404/422 otherwise); rejects the same piece
appearing twice in the same programme (409). `ordine` is not DB-unique per
event/rehearsal — reordering the programme is expected to be a common
operation, and enforcing uniqueness would force multi-step shuffles to
avoid transient conflicts, for a constraint the application layer can keep
sane either way. Lessons have no repertoire (only a calendar/roster).

### Corsi (music courses)

Standard CRUD under `/corsi`.

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/corsi/?banda_codice={b}&anno={a}&tipo_corso_codice={c}` | List courses, filterable by band, year, and/or type (paginated) | `corsi:read` |
| `GET` | `/corsi/{id}` | Get a course by ID | `corsi:read` |
| `POST` | `/corsi/` | Create a course | `corsi:write` |
| `PATCH` | `/corsi/{id}` | Update a course | `corsi:write` |
| `DELETE` | `/corsi/{id}` | Delete a course (204) | `corsi:write` |

`Corso` requires an existing `tipo_corso_codice` (404). Its optional
`coordinatore_persona_id`/`insegnante_persona_id` are validated if provided
(404) and reference `Persona` directly, not `Socio` — consistent with
`Ricevuta.persona_id`, since a teacher can be an external hire, not
necessarily a member. No uniqueness constraint on
`(tipo_corso_codice, anno, banda_codice)`: parallel courses of the same type
in the same year (e.g. different levels, different teachers) are a legitimate
case, not an anomaly to block.

### Allievi

Standard CRUD under `/allievi` (`corsi:read`/`corsi:write`).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/allievi/?banda_codice={b}` | List students, filterable by band (joins through `Persona`, paginated) | `corsi:read` |
| `GET` | `/allievi/{id}` | Get a student by ID | `corsi:read` |
| `POST` | `/allievi/` | Create a student record | `corsi:write` |
| `PATCH` | `/allievi/{id}` | Update a student record | `corsi:write` |
| `DELETE` | `/allievi/{id}` | Delete a student record (204) | `corsi:write` |

`Allievo` requires an existing `persona_id` (404); rejects a `Persona`
already linked to another `Allievo` record (409) and a duplicate
`codice_allievo` (409).

### Lezioni

Standard CRUD under `/lezioni` (`corsi:read`/`corsi:write`).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/lezioni/?corso_id={id}` | List lessons for a course (paginated) | `corsi:read` |
| `GET` | `/lezioni/{id}` | Get a lesson by ID | `corsi:read` |
| `POST` | `/lezioni/` | Create a lesson | `corsi:write` |
| `PATCH` | `/lezioni/{id}` | Update a lesson | `corsi:write` |
| `DELETE` | `/lezioni/{id}` | Delete a lesson (204) | `corsi:write` |

`Lezione` requires an existing `corso_id` (404, always required — a lesson
never stands alone); `indirizzo_id` is optional and validated if provided
(404). A lesson's roster/attendance is at `GET /presenze/lezione/{id}` (see
Presenze above), gated by `corsi:read`/`corsi:write` like the rest of this
section, not `servizi:*`.

### Iscrizioni corso

Standard CRUD under `/iscrizioni-corso` (`corsi:read`/`corsi:write`).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/iscrizioni-corso/?corso_id={c}&persona_id={p}` | List enrolments, filterable by course and/or person (paginated) | `corsi:read` |
| `GET` | `/iscrizioni-corso/{id}` | Get an enrolment by ID | `corsi:read` |
| `POST` | `/iscrizioni-corso/` | Create an enrolment | `corsi:write` |
| `PATCH` | `/iscrizioni-corso/{id}` | Update an enrolment | `corsi:write` |
| `DELETE` | `/iscrizioni-corso/{id}` | Delete an enrolment (204) | `corsi:write` |

`IscrizioneCorso` requires an existing `corso_id`, `persona_id`,
`stato_iscrizione_corso_codice`, and — if provided — `documento_id` (404
otherwise). No uniqueness constraint on `(persona_id, corso_id)`: a person
can be re-enrolled after a cancelled enrolment.

### Pagamenti corso

Standard CRUD under `/pagamenti-corso` (`corsi:read`/`corsi:write`).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/pagamenti-corso/?iscrizione_corso_id={id}` | List payments for an enrolment (paginated) | `corsi:read` |
| `GET` | `/pagamenti-corso/{id}` | Get a payment by ID | `corsi:read` |
| `POST` | `/pagamenti-corso/` | Record a payment — auto-posts a `Ricevuta` + `FlussoCassa` (see below) | `corsi:write` |
| `PATCH` | `/pagamenti-corso/{id}` | Update a payment | `corsi:write` |
| `DELETE` | `/pagamenti-corso/{id}` | Delete a payment (204) | `corsi:write` |

`PagamentoCorso` requires an existing `iscrizione_corso_id` (404). On
`POST`, the service resolves the enrolment's (banda, anno) from its
`Corso`, looks up `ConfigurazioneBandaAnno.voce_contabilita_corsi_id` for
that pair (`422` — `ConfigurazioneContabileCorsiMancanteError` — if unset),
and creates a `RISCOSSIONE` `Ricevuta` plus a `FlussoCassa` of `tipo`
`AUTO_PAGAMENTO_CORSO` (natura Banca) referencing it — same auto-posting
pattern already used by `Iscrizione`/`AUTO_ISCRIZIONE` for membership
quotes, applied here to course fees.

### Catalogo programmi

Standard CRUD under `/catalogo-programmi` (`corsi:read`/`corsi:write` — not
`lookup:*`, since it's compiled by teaching staff, not administrators).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/catalogo-programmi/?tipo_corso_codice={t}&categoria_codice={c}&livello={l}&attiva={a}` | List catalogue items, filterable (paginated) | `corsi:read` |
| `GET` | `/catalogo-programmi/{id}` | Get a catalogue item by ID | `corsi:read` |
| `POST` | `/catalogo-programmi/` | Create a catalogue item (409 on duplicate `(tipo_corso_codice, testo)`) | `corsi:write` |
| `PATCH` | `/catalogo-programmi/{id}` | Update a catalogue item, including soft-delete (`attiva=False`) | `corsi:write` |

No `DELETE`: removing an item from the catalogue is a soft-delete
(`attiva=False`) via `PATCH`, never a hard delete — historical references from
already-compiled `SchedaAlunnoVoce` rows must never be invalidated. Its
companion lookup, **categorie voce programma**, is plain reference data
(`/categorie-voce-programma`, `lookup:*`) — see
[Tabelle dimensione](#tabelle-dimensione-lookups).

### Schede alunno (row-level authorization)

The personal record of a student enrolled in a course (`SchedaAlunno`, one per
`IscrizioneCorso` — `iscrizione_corso_id` is UNIQUE, 409 on duplicate). It holds
the student's programme (`voci`), attached teaching material (`materiali`),
and their own self-assessment diary (`autovalutazioni`) — see
[Domain model](#domain-model) above for each sub-resource.

This is the first endpoint in the project whose authorization is **not** purely
resource:action. A student holds no `corsi:*` permission at all and must still
read their own record — and only their own. That check cannot be expressed as a
permission row, so it lives in `app/services/rbac_row_level.py` as pure
functions (user + row data → decision), unit-testable without HTTP:

Read and write have different scopes:

| Caller | Read | Write |
|---|---|---|
| superuser | any record | any record |
| `corsi:write` **and** teacher/coordinator of *this* course (`corso.insegnante_persona_id`/`coordinatore_persona_id`) | any record | this course's records |
| `corsi:write` but not teacher/coordinator of *this* course | any record | 403 |
| the student the record refers to (`utenti.persona_id` == `iscrizioni_corso.persona_id`) | own record only | 403 |
| anyone else — including an authenticated user with no linked `Persona` | 403 | 403 |

Read stays permission-only (any `corsi:read` holder reads any record) — the
card that introduced this restriction only asked to scope *writing* to "one's
own courses", and `GET /schede-alunno/{id}`/list never call into
`rbac_row_level` in the first place, so narrowing read would be a separate,
unrequested change. Write is not: `corsi:write` alone is no longer sufficient,
`assert_puo_scrivere_scheda` additionally requires the caller's linked
`Persona` to be the teacher or coordinator of the specific course the record
belongs to (resolved via `scheda → iscrizione_corso → corso`). The superuser
bypass mirrors the existing pattern in `permessi_archivio.require_write`.

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/schede-alunno/me/{iscrizione_corso_id}` | Read the record for that enrolment, if entitled | row-level only |
| `GET` | `/schede-alunno/?iscrizione_corso_id={id}` | List records (paginated) | `corsi:read` |
| `GET` | `/schede-alunno/{id}` | Get a record by ID | `corsi:read` |
| `POST` | `/schede-alunno/` | Create a record | `corsi:write` |
| `PATCH` | `/schede-alunno/{id}` | Update a record | `corsi:write` |
| `DELETE` | `/schede-alunno/{id}` | Delete a record (204) | `corsi:write` |

The student's route is deliberately **separate** from `GET /schede-alunno/{id}`
rather than one endpoint hosting both rules: a single route would have to admit
any authenticated caller and deny from inside its body, so the router's
declarative guard could no longer state the requirement. It is also keyed by
`iscrizione_corso_id` — a student knows their own enrolment, not the ID of a
record they have never seen.

On `/me/...` authorization is evaluated *before* the record is looked up, so an
unauthorized caller gets 403 whether or not a record exists and cannot use the
status code to probe. `aggiornato_da_persona_id` (audit) is always taken from
the authenticated principal, never from the payload.

#### Voci di programma

Nested under a record; no standalone list endpoint — reading a record's voci
arrives embedded in `SchedaAlunnoResponse.voci` (ordered by `ordine`).

| Method | Path | Description | Permission |
|---|---|---|---|
| `POST` | `/schede-alunno/{scheda_alunno_id}/voci` | Add a catalogue item to the record's programme | `corsi:write` |
| `PATCH` | `/schede-alunno/{scheda_alunno_id}/voci/{voce_id}` | Update `stato`/`dettaglio`/`ordine` | `corsi:write` |
| `DELETE` | `/schede-alunno/{scheda_alunno_id}/voci/{voce_id}` | Remove a voce (204) | `corsi:write` |

Authorization reuses `assert_puo_scrivere_scheda` unchanged — no new rule.
`voce_catalogo_id` must reference an existing, `attiva` catalogue item whose
`tipo_corso_codice` matches the record's course (404/422 otherwise). Every
creation and every `stato` change writes an append-only row to the storico
(below); a `PATCH` that leaves `stato` untouched writes nothing.

#### Materiale didattico

Also nested; reading arrives embedded in `SchedaAlunnoResponse.materiali`.

| Method | Path | Description | Permission |
|---|---|---|---|
| `POST` | `/schede-alunno/{scheda_alunno_id}/materiali/file` | Upload a file (`multipart/form-data`: `titolo`, `file`) | `corsi:write` |
| `POST` | `/schede-alunno/{scheda_alunno_id}/materiali/link` | Attach an external link (`titolo`, `url`) | `corsi:write` |
| `GET` | `/schede-alunno/{scheda_alunno_id}/materiali/{materiale_id}/download` | Download a file material as attachment | row-level (`assert_puo_leggere_scheda`) |
| `DELETE` | `/schede-alunno/{scheda_alunno_id}/materiali/{materiale_id}` | Delete a material — hard delete, also removes the file from storage (204) | `corsi:write` |

A file/link material is a two-branch exclusive arc — never both, enforced by
a DB `CHECK`. Upload rejects an extension outside the whitelist (`422`,
`pdf`/`docx`/`jpg`/`jpeg`/`png`/`mp3`/`m4a`/`wav`/`avi`/`mp4`/`mscz`/`sib`) or
over 20 MB (`422`). Download is the *one* endpoint on this router gated by
row-level authorization instead of the declarative `corsi:read` guard: the
owning student (who never has `corsi:read`) can download their own material
too, same as `GET /schede-alunno/me/{iscrizione_corso_id}`; `404` if the
material is a link, not a file (`MaterialeNonFileError`).

#### Autovalutazioni (student-authored, `/me` only)

The **only** write the student performs on their own record — a perimeter
deliberately *not* derived from `assert_puo_scrivere_scheda`: `corsi:write`
grants **no** access here, not even to the course's own teacher/coordinator,
because this is the student's private diary, not staff-authored content. See
`assert_puo_scrivere_autovalutazione` in `app/services/rbac_row_level.py`.

| Method | Path | Description | Authorization |
|---|---|---|---|
| `POST` | `/schede-alunno/me/{iscrizione_corso_id}/autovalutazioni` | Add an entry (`testo`) | owning student (or superuser) only |
| `PATCH` | `/schede-alunno/me/{iscrizione_corso_id}/autovalutazioni/{id}` | Edit an entry — sets `data_modifica` | owning student (or superuser) only |
| `DELETE` | `/schede-alunno/me/{iscrizione_corso_id}/autovalutazioni/{id}` | Remove an entry (204) | owning student (or superuser) only |

Reading arrives embedded in `SchedaAlunnoResponse.autovalutazioni` (newest
first), visible to whoever can read the record at all — staff with
`corsi:read` and the owning student. `persona_id` (author) is always taken
from the authenticated principal, never from the payload.

#### Storico dei cambi di stato (read-only)

An append-only log of every `stato` transition on the record's voci, written
automatically by the voci endpoints above (never directly writable). Kept
even after the voce itself is deleted (`scheda_alunno_voce_id` cleared, the
row stays) or its catalogue item is later removed from the catalogue
(`voce_testo` falls back to `null` instead of the row disappearing or the
request failing).

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/schede-alunno/{scheda_alunno_id}/storico-voci` | Storico for a record, newest first (paginated) | `corsi:read` |
| `GET` | `/schede-alunno/me/{iscrizione_corso_id}/storico-voci` | The caller's own record's storico, if entitled (paginated) | row-level (`assert_puo_leggere_scheda`) |

Each row is enriched with who made the change (`modificato_da`, resolved from
the real `Persona` FK) and the catalogue item's text at read time
(`voce_testo`, resolved separately since `voce_catalogo_id` is a
denormalized plain integer, not a FK — see [Domain model](#domain-model)).

### Portale alunno (student self-service)

A second row-level surface, entirely separate from the staff-facing
`/corsi`, `/allievi`, `/lezioni`, `/presenze`, `/iscrizioni-corso`,
`/pagamenti-corso` routers (same rationale as `/schede-alunno/me/...`): no
`corsi:*` permission is ever required or granted here — the only
authorization is being the `Persona` the enrolment belongs to
(`rbac_row_level.assert_e_titolare_iscrizione`, reusing the same
comparison as `e_alunno_della_scheda`). Everything lives under `/me`
because it's a cross-cutting entry point, not an extension of one CRUD
resource: a student discovers their own enrolments and navigates from
there to that enrolment's calendar, attendance, and payments.

| Method | Path | Description |
|---|---|---|
| `GET` | `/me/iscrizioni-corso` | The caller's own course enrolments (paginated) |
| `GET` | `/me/iscrizioni-corso/{id}/lezioni` | Lesson calendar for one of the caller's enrolments (paginated) |
| `GET` | `/me/iscrizioni-corso/{id}/presenze` | The caller's own attendance for that enrolment (paginated) |
| `GET` | `/me/iscrizioni-corso/{id}/pagamenti` | The caller's own payments for that enrolment (paginated) |

Every `{id}`-scoped endpoint loads the enrolment (404 if absent), checks
ownership (403 if it belongs to someone else), then queries the child
resource — `403` before `404` is not the ordering here (unlike
`/schede-alunno/me/...`) because the enrolment itself is the thing being
looked up, not a separate row gated behind it. `GET /me/iscrizioni-corso`
additionally requires the caller to have a `Persona` linked at all
(`assert_ha_persona_collegata`) — a management-only `Utente` with no
`persona_id` is never a student, regardless of which enrolment it asks
about.

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
`/stati-iscrizione`, `/tipi-corso`, `/stati-iscrizione-corso`,
`/categorie-voce-programma`. All gated by the shared `lookup:read`/`lookup:write`
permission.

| Method | Path | Description | Permission |
|---|---|---|---|
| `GET` | `/{lookup}/` | List entries (paginated) | `lookup:read` |
| `GET` | `/{lookup}/{codice}` | Get an entry by code | `lookup:read` |
| `POST` | `/{lookup}/` | Create an entry (409 on duplicate code) | `lookup:write` |
| `PATCH` | `/{lookup}/{codice}` | Update an entry | `lookup:write` |
| `DELETE` | `/{lookup}/{codice}` | Delete an entry (204) | `lookup:write` |

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
| `corsi:read` | Visualizzare i corsi musicali |
| `corsi:write` | Gestire i corsi musicali |
| `lookup:read` | Visualizzare le tabelle dimensione |
| `lookup:write` | Gestire le tabelle dimensione |

Ogni **macro-sezione** dell'archivio (`/macro-sezioni`) porta inoltre un
proprio prefisso di permesso dedicato, seedato via migrazione insieme alla
macro-sezione stessa, in alternativa al generico `archivio:*` (usato invece
per gli aggregati che non appartengono a nessuna macro-sezione: spartiti,
nome_parti, documenti senza sotto-cartella):

| Macro-sezione | Prefisso permesso |
|---|---|
| Certificazioni Uniche | `certificazioni:read/write` |
| Verbali e Libro Soci | `verbali:read/write` |
| Concorsi e Bandi | `concorsi:read/write` |
| Documenti Amministrativi | `documenti_admin:read/write` |

**Permission enforcement status:**

Every domain endpoint now carries a `require_permission()` guard (or, for
the archivio, the dynamic `permessi_archivio.require_read`/`require_write`
described above) — the audit/uniform-enforcement pass (card #194) closed
the gaps that used to leave `anagrafica:*`, `iscrizioni:*`, `servizi:*`, and
`archivio:*` defined but unchecked. All domain endpoints also **require
authentication** (`Depends(get_current_user)`): without a valid session or
JWT, responses are `401`. The `Ospite` role seeded for self-registration
(`POST /auth/register`) is granted read-only permissions across the board
(including `lookup:read`), excluding `contabilita:*` and admin
(`utenti:*`/`ruoli:*`).

Two endpoints sit outside the resource:action model entirely and use
**row-level** authorization instead — see [Schede alunno](#schede-alunno-row-level-authorization)
and [Portale alunno](#portale-alunno-student-self-service) above.

*Superuser* accounts bypass all permission checks, including row-level ones.

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
  esterno, contatto, servizio, ricevuta, iscrizione, allievo, iscrizione_corso)
  — e.g. annual financial reports populated from contabilità data, assembly
  minutes. Mostly need a new provider plus a template body, not new backend
  plumbing.
- Bulk import of members and externals from Excel files (via async worker)
- Auto-posting of service-related receipts (compensi/riscossioni) to
  `FlussoCassa`, on the pattern already used for `AUTO_ISCRIZIONE` and, since
  `PagamentoCorso`, for `AUTO_PAGAMENTO_CORSO` too — the latter is a working
  precedent for the missing piece (a dedicated
  `ConfigurazioneBandaAnno.voce_contabilita_*_id` per use case plus a fixed
  `natura_flusso`/sign), but no such column exists yet for
  compensi/riscossioni; deliberately left out of the `Ricevuta.persona_id`
  generalization pending that design.
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
