from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.documento import DocumentoNotFoundError
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.lookup import LookupNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.models.lookups import StatoIscrizioneCorso
from app.repositories.corso_repository import CorsoRepository
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.iscrizione_corso import (
    IscrizioneCorsoCreate,
    IscrizioneCorsoResponse,
    IscrizioneCorsoUpdate,
)
from app.services.iscrizione_corso_service import IscrizioneCorsoService

router = APIRouter(prefix="/iscrizioni-corso", tags=["iscrizioni-corso"])

_FK_ERRORS = (
    CorsoNotFoundError,
    PersonaNotFoundError,
    LookupNotFoundError,
    DocumentoNotFoundError,
)


def get_service(db: AsyncSession = Depends(get_db)) -> IscrizioneCorsoService:
    return IscrizioneCorsoService(
        IscrizioneCorsoRepository(db),
        CorsoRepository(db),
        PersonaRepository(db),
        LookupRepository(db, StatoIscrizioneCorso),
        DocumentoRepository(db),
    )


@router.get(
    "/",
    response_model=PagedResponse[IscrizioneCorsoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_iscrizioni_corso(
    corso_id: int | None = Query(None),
    persona_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: IscrizioneCorsoService = Depends(get_service),
) -> PagedResponse[IscrizioneCorsoResponse]:
    return await service.get_all(params, corso_id=corso_id, persona_id=persona_id)


@router.get(
    "/{iscrizione_corso_id}",
    response_model=IscrizioneCorsoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_iscrizione_corso(
    iscrizione_corso_id: int, service: IscrizioneCorsoService = Depends(get_service)
) -> IscrizioneCorsoResponse:
    try:
        return await service.get_by_id(iscrizione_corso_id)
    except IscrizioneCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=IscrizioneCorsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_iscrizione_corso(
    data: IscrizioneCorsoCreate, service: IscrizioneCorsoService = Depends(get_service)
) -> IscrizioneCorsoResponse:
    try:
        return await service.create(data)
    except _FK_ERRORS as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{iscrizione_corso_id}",
    response_model=IscrizioneCorsoResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_iscrizione_corso(
    iscrizione_corso_id: int,
    data: IscrizioneCorsoUpdate,
    service: IscrizioneCorsoService = Depends(get_service),
) -> IscrizioneCorsoResponse:
    try:
        return await service.update(iscrizione_corso_id, data)
    except (IscrizioneCorsoNotFoundError, *_FK_ERRORS) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{iscrizione_corso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def delete_iscrizione_corso(
    iscrizione_corso_id: int, service: IscrizioneCorsoService = Depends(get_service)
) -> None:
    try:
        await service.delete(iscrizione_corso_id)
    except IscrizioneCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
