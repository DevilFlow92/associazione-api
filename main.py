from fastapi import FastAPI

from app.api.v1.iscrizioni import router as iscrizioni_router
from app.api.v1.soci import router as soci_router

app = FastAPI(
    title="Associazione API",
    description="REST API backend for music association management",
    version="0.1.0",
)

app.include_router(soci_router, prefix="/api/v1")
app.include_router(iscrizioni_router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
