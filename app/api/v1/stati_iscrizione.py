from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import StatoIscrizione
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    StatoIscrizioneCreate,
    StatoIscrizioneResponse,
    StatoIscrizioneUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/stati-iscrizione", tags=["stati-iscrizione"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[StatoIscrizioneResponse]:
    return LookupService(
        LookupRepository(db, StatoIscrizione),
        StatoIscrizioneResponse,
        "Stato iscrizione",
    )


@router.get("/", response_model=PagedResponse[StatoIscrizioneResponse])
async def list_stati_iscrizione(
    params: PageParams = Depends(),
    service: LookupService[StatoIscrizioneResponse] = Depends(get_service),
) -> PagedResponse[StatoIscrizioneResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=StatoIscrizioneResponse)
async def get_stato_iscrizione(
    codice: int, service: LookupService[StatoIscrizioneResponse] = Depends(get_service)
) -> StatoIscrizioneResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=StatoIscrizioneResponse, status_code=status.HTTP_201_CREATED
)
async def create_stato_iscrizione(
    data: StatoIscrizioneCreate,
    service: LookupService[StatoIscrizioneResponse] = Depends(get_service),
) -> StatoIscrizioneResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=StatoIscrizioneResponse)
async def update_stato_iscrizione(
    codice: int,
    data: StatoIscrizioneUpdate,
    service: LookupService[StatoIscrizioneResponse] = Depends(get_service),
) -> StatoIscrizioneResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stato_iscrizione(
    codice: int, service: LookupService[StatoIscrizioneResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
