from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.sotto_cartella_repository import MacroSezioneRepository
from app.schemas.macro_sezione import MacroSezioneResponse
from app.services.macro_sezione_service import MacroSezioneService

router = APIRouter(prefix="/macro-sezioni", tags=["macro-sezioni"])


def get_service(db: AsyncSession = Depends(get_db)) -> MacroSezioneService:
    return MacroSezioneService(MacroSezioneRepository(db))


@router.get("/", response_model=list[MacroSezioneResponse])
async def list_macro_sezioni(
    service: MacroSezioneService = Depends(get_service),
) -> list[MacroSezioneResponse]:
    """Catalogo delle macro-sezioni dell'archivio (sola lettura: dati seed-ati)."""
    return await service.get_all()
