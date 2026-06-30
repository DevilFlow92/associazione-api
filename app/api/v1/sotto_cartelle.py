from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.exceptions.sotto_cartella import (
    SottoCartellaDuplicateNomeError,
    SottoCartellaMacroSezioneNotFoundError,
    SottoCartellaNotFoundError,
)
from app.models.utente import Utente
from app.repositories.sotto_cartella_repository import (
    MacroSezioneRepository,
    SottoCartellaRepository,
)
from app.schemas.sotto_cartella import (
    SottoCartellaCreate,
    SottoCartellaResponse,
    SottoCartellaUpdate,
)
from app.services.sotto_cartella_service import SottoCartellaService

router = APIRouter(prefix="/sotto-cartelle", tags=["sotto-cartelle"])


def get_service(db: AsyncSession = Depends(get_db)) -> SottoCartellaService:
    return SottoCartellaService(SottoCartellaRepository(db), MacroSezioneRepository(db))


@router.get("/", response_model=list[SottoCartellaResponse])
async def list_sotto_cartelle(
    macro_sezione_codice: int,
    service: SottoCartellaService = Depends(get_service),
) -> list[SottoCartellaResponse]:
    try:
        return await service.get_all_for_macro_sezione(macro_sezione_codice)
    except SottoCartellaMacroSezioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/", response_model=SottoCartellaResponse, status_code=status.HTTP_201_CREATED
)
async def create_sotto_cartella(
    data: SottoCartellaCreate,
    user: Utente = Depends(get_current_user),
    service: SottoCartellaService = Depends(get_service),
) -> SottoCartellaResponse:
    try:
        return await service.create(data, user)
    except SottoCartellaMacroSezioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except SottoCartellaDuplicateNomeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{id}", response_model=SottoCartellaResponse)
async def update_sotto_cartella(
    id: int,
    data: SottoCartellaUpdate,
    user: Utente = Depends(get_current_user),
    service: SottoCartellaService = Depends(get_service),
) -> SottoCartellaResponse:
    try:
        return await service.update(id, data, user)
    except SottoCartellaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except SottoCartellaDuplicateNomeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sotto_cartella(
    id: int,
    user: Utente = Depends(get_current_user),
    service: SottoCartellaService = Depends(get_service),
) -> None:
    try:
        await service.delete(id, user)
    except SottoCartellaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
