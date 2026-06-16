from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import SezioneRendiconto
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    SezioneRendicontoCreate,
    SezioneRendicontoResponse,
    SezioneRendicontoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/sezioni-rendiconto", tags=["sezioni-rendiconto"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[SezioneRendicontoResponse]:
    return LookupService(
        LookupRepository(db, SezioneRendiconto),
        SezioneRendicontoResponse,
        "Sezione rendiconto",
    )


@router.get("/", response_model=PagedResponse[SezioneRendicontoResponse])
async def list_sezioni_rendiconto(
    params: PageParams = Depends(),
    service: LookupService[SezioneRendicontoResponse] = Depends(get_service),
) -> PagedResponse[SezioneRendicontoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=SezioneRendicontoResponse)
async def get_sezione_rendiconto(
    codice: int,
    service: LookupService[SezioneRendicontoResponse] = Depends(get_service),
) -> SezioneRendicontoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=SezioneRendicontoResponse, status_code=status.HTTP_201_CREATED
)
async def create_sezione_rendiconto(
    data: SezioneRendicontoCreate,
    service: LookupService[SezioneRendicontoResponse] = Depends(get_service),
) -> SezioneRendicontoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=SezioneRendicontoResponse)
async def update_sezione_rendiconto(
    codice: int,
    data: SezioneRendicontoUpdate,
    service: LookupService[SezioneRendicontoResponse] = Depends(get_service),
) -> SezioneRendicontoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sezione_rendiconto(
    codice: int,
    service: LookupService[SezioneRendicontoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
