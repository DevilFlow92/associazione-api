from fastapi import FastAPI

import app.models  # noqa: F401
from app.api.v1.documenti import router as documenti_router
from app.api.v1.iscrizioni import router as iscrizioni_router
from app.api.v1.soci import router as soci_router
from app.api.v1.templates import router as template_router
from app.core.logging import setup_logging
from app.core.middleware import RequestMiddleware

setup_logging()

app = FastAPI(
    title="Associazione API",
    description="REST API backend for music association management",
    version="0.1.0",
)

app.add_middleware(RequestMiddleware)

app.include_router(soci_router, prefix="/api/v1")
app.include_router(iscrizioni_router, prefix="/api/v1")
app.include_router(documenti_router, prefix="/api/v1")
app.include_router(template_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
