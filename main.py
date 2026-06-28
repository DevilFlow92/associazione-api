from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from app.api.deps import get_current_user
from app.api.v1.auth import router as auth_router
from app.api.v1.bande import public_router as bande_public_router
from app.api.v1.bande import router as bande_router
from app.api.v1.check_quote import router as check_quote_router
from app.api.v1.comuni import router as comuni_router
from app.api.v1.configurazione_banda_anno import (
    router as configurazione_banda_anno_router,
)
from app.api.v1.contatti import router as contatti_router
from app.api.v1.documenti import router as documenti_router
from app.api.v1.esterni import router as esterni_router
from app.api.v1.flussi_cassa import router as flussi_cassa_router
from app.api.v1.indirizzi import router as indirizzi_router
from app.api.v1.iscrizioni import router as iscrizioni_router
from app.api.v1.nature_flusso import router as nature_flusso_router
from app.api.v1.permessi import router as permessi_router
from app.api.v1.persone import router as persone_router
from app.api.v1.province import router as province_router
from app.api.v1.regioni import router as regioni_router
from app.api.v1.rendiconto import router as rendiconto_router
from app.api.v1.ricevute import router as ricevute_router
from app.api.v1.ruoli import router as ruoli_router
from app.api.v1.ruoli_banda import router as ruoli_banda_router
from app.api.v1.ruoli_contatto import router as ruoli_contatto_router
from app.api.v1.servizi import router as servizi_router
from app.api.v1.sezioni_rendiconto import router as sezioni_rendiconto_router
from app.api.v1.soci import router as soci_router
from app.api.v1.sottovoci_rendiconto import router as sottovoci_rendiconto_router
from app.api.v1.spartiti import router as spartiti_router
from app.api.v1.stati import router as stati_router
from app.api.v1.stati_iscrizione import router as stati_iscrizione_router
from app.api.v1.strumenti import router as strumenti_router
from app.api.v1.templates import router as template_router
from app.api.v1.tipi_documento import router as tipi_documento_router
from app.api.v1.tipi_indirizzo import router as tipi_indirizzo_router
from app.api.v1.tipi_spartito import router as tipi_spartito_router
from app.api.v1.utenti import router as utenti_router
from app.api.v1.voci_contabilita import router as voci_contabilita_router
from app.api.v1.voci_rendiconto import router as voci_rendiconto_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestMiddleware
from app.exceptions.auth import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.exceptions.flusso_cassa import (
    AnnoChiusoError,
    FlussoTrasferimentoNonModificabileError,
    NaturaFlussoNotFoundError,
    TrasferimentoNaturaUgualeError,
)
from app.exceptions.iscrizione import ConfigurazioneContabileMancanteError
from app.exceptions.lookup import LookupDuplicateCodiceError, LookupNotFoundError

# Configura logging prima di tutto il resto.
# In development: output colorato human-readable.
# In staging/production: JSON strutturato per log aggregators.
setup_logging(
    level="DEBUG" if settings.app_debug else "INFO",
    render_json=settings.app_env != "development",
)

logger = get_logger(__name__)

app = FastAPI(
    title="Associazione API",
    description="REST API backend for music association management",
    version="0.1.0",
)

app.add_middleware(RequestMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://bandapp.cosequences.com",
        "https://associazione-api.cosequences.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Le tabelle dimensione (lookup) condividono due eccezioni generiche: le
# mappiamo in modo centralizzato così i 9 router restano minimali.
@app.exception_handler(AnnoChiusoError)
async def anno_chiuso_handler(request: Request, exc: AnnoChiusoError) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(ConfigurazioneContabileMancanteError)
async def configurazione_contabile_mancante_handler(
    request: Request, exc: ConfigurazioneContabileMancanteError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(TrasferimentoNaturaUgualeError)
async def trasferimento_natura_uguale_handler(
    request: Request, exc: TrasferimentoNaturaUgualeError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(NaturaFlussoNotFoundError)
async def natura_flusso_not_found_handler(
    request: Request, exc: NaturaFlussoNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.exception_handler(FlussoTrasferimentoNonModificabileError)
async def flusso_trasferimento_non_modificabile_handler(
    request: Request, exc: FlussoTrasferimentoNonModificabileError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(LookupNotFoundError)
async def lookup_not_found_handler(
    request: Request, exc: LookupNotFoundError
) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(LookupDuplicateCodiceError)
async def lookup_duplicate_handler(
    request: Request, exc: LookupDuplicateCodiceError
) -> JSONResponse:
    return JSONResponse(status_code=409, content={"detail": str(exc)})


# Violazioni di integrità del DB (es. codice lookup inesistente in una FK, o
# valore duplicato) → 409 invece di un 500 opaco.
@app.exception_handler(IntegrityError)
async def integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    logger.warning("integrity error", error=str(exc.orig))
    return JSONResponse(
        status_code=409,
        content={
            "detail": (
                "Violazione di un vincolo di integrità "
                "(chiave esterna inesistente o valore duplicato)"
            )
        },
    )


# Errori di autenticazione/autorizzazione → 401/403. I router gestiscono già
# i casi inline, ma questi handler coprono le eccezioni propagate dai service.
@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(
    request: Request, exc: InvalidCredentialsError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(InvalidTokenError)
async def invalid_token_handler(
    request: Request, exc: InvalidTokenError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(InactiveUserError)
async def inactive_user_handler(
    request: Request, exc: InactiveUserError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


# ── Autenticazione & RBAC ────────────────────────────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(utenti_router, prefix="/api/v1")
app.include_router(ruoli_router, prefix="/api/v1")
app.include_router(permessi_router, prefix="/api/v1")

_auth = [Depends(get_current_user)]

# ── Anagrafica (entità core) ─────────────────────────────────────────────────
app.include_router(persone_router, prefix="/api/v1", dependencies=_auth)
app.include_router(indirizzi_router, prefix="/api/v1", dependencies=_auth)
app.include_router(contatti_router, prefix="/api/v1", dependencies=_auth)
app.include_router(soci_router, prefix="/api/v1", dependencies=_auth)
app.include_router(esterni_router, prefix="/api/v1", dependencies=_auth)
app.include_router(iscrizioni_router, prefix="/api/v1", dependencies=_auth)

# ── Eventi & ricevute ────────────────────────────────────────────────────────
app.include_router(servizi_router, prefix="/api/v1", dependencies=_auth)
app.include_router(ricevute_router, prefix="/api/v1", dependencies=_auth)

# ── Contabilità ──────────────────────────────────────────────────────────────
app.include_router(voci_contabilita_router, prefix="/api/v1", dependencies=_auth)
app.include_router(flussi_cassa_router, prefix="/api/v1", dependencies=_auth)
app.include_router(rendiconto_router, prefix="/api/v1", dependencies=_auth)
app.include_router(check_quote_router, prefix="/api/v1", dependencies=_auth)
app.include_router(
    configurazione_banda_anno_router, prefix="/api/v1", dependencies=_auth
)

# ── Tabelle dimensione (lookup) ──────────────────────────────────────────────
app.include_router(stati_router, prefix="/api/v1", dependencies=_auth)
app.include_router(regioni_router, prefix="/api/v1", dependencies=_auth)
app.include_router(province_router, prefix="/api/v1", dependencies=_auth)
app.include_router(comuni_router, prefix="/api/v1", dependencies=_auth)
app.include_router(strumenti_router, prefix="/api/v1", dependencies=_auth)
app.include_router(tipi_indirizzo_router, prefix="/api/v1", dependencies=_auth)
app.include_router(bande_public_router, prefix="/api/v1")  # no auth — registration flow
app.include_router(bande_router, prefix="/api/v1", dependencies=_auth)
app.include_router(ruoli_contatto_router, prefix="/api/v1", dependencies=_auth)
app.include_router(ruoli_banda_router, prefix="/api/v1", dependencies=_auth)
app.include_router(sezioni_rendiconto_router, prefix="/api/v1", dependencies=_auth)
app.include_router(voci_rendiconto_router, prefix="/api/v1", dependencies=_auth)
app.include_router(sottovoci_rendiconto_router, prefix="/api/v1", dependencies=_auth)
app.include_router(nature_flusso_router, prefix="/api/v1", dependencies=_auth)
app.include_router(tipi_documento_router, prefix="/api/v1", dependencies=_auth)
app.include_router(tipi_spartito_router, prefix="/api/v1", dependencies=_auth)
app.include_router(stati_iscrizione_router, prefix="/api/v1", dependencies=_auth)

# ── Archivio documentale (file) ──────────────────────────────────────────────
app.include_router(documenti_router, prefix="/api/v1", dependencies=_auth)
app.include_router(template_router, prefix="/api/v1", dependencies=_auth)
app.include_router(spartiti_router, prefix="/api/v1", dependencies=_auth)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


logger.info(
    "application started",
    env=settings.app_env,
    debug=settings.app_debug,
)
