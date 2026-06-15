from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

import app.models  # noqa: F401
from app.api.v1.bande import router as bande_router
from app.api.v1.comuni import router as comuni_router
from app.api.v1.contatti import router as contatti_router
from app.api.v1.documenti import router as documenti_router
from app.api.v1.esterni import router as esterni_router
from app.api.v1.indirizzi import router as indirizzi_router
from app.api.v1.persone import router as persone_router
from app.api.v1.province import router as province_router
from app.api.v1.regioni import router as regioni_router
from app.api.v1.ruoli_banda import router as ruoli_banda_router
from app.api.v1.ruoli_contatto import router as ruoli_contatto_router
from app.api.v1.soci import router as soci_router
from app.api.v1.stati import router as stati_router
from app.api.v1.strumenti import router as strumenti_router
from app.api.v1.templates import router as template_router
from app.api.v1.tipi_indirizzo import router as tipi_indirizzo_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.core.middleware import RequestMiddleware
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


# Le tabelle dimensione (lookup) condividono due eccezioni generiche: le
# mappiamo in modo centralizzato così i 9 router restano minimali.
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


# ── Anagrafica (entità core) ─────────────────────────────────────────────────
app.include_router(persone_router, prefix="/api/v1")
app.include_router(indirizzi_router, prefix="/api/v1")
app.include_router(contatti_router, prefix="/api/v1")
app.include_router(soci_router, prefix="/api/v1")
app.include_router(esterni_router, prefix="/api/v1")

# ── Tabelle dimensione (lookup) ──────────────────────────────────────────────
app.include_router(stati_router, prefix="/api/v1")
app.include_router(regioni_router, prefix="/api/v1")
app.include_router(province_router, prefix="/api/v1")
app.include_router(comuni_router, prefix="/api/v1")
app.include_router(strumenti_router, prefix="/api/v1")
app.include_router(tipi_indirizzo_router, prefix="/api/v1")
app.include_router(bande_router, prefix="/api/v1")
app.include_router(ruoli_contatto_router, prefix="/api/v1")
app.include_router(ruoli_banda_router, prefix="/api/v1")

# ── Repository documentale (file) ────────────────────────────────────────────
app.include_router(documenti_router, prefix="/api/v1")
app.include_router(template_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


logger.info(
    "application started",
    env=settings.app_env,
    debug=settings.app_debug,
)
