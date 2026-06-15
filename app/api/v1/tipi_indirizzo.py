from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import TipoIndirizzo
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    TipoIndirizzoCreate,
    TipoIndirizzoResponse,
    TipoIndirizzoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/tipi-indirizzo", tags=["tipi-indirizzo"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[TipoIndirizzoResponse]:
    return LookupService(
        LookupRepository(db, TipoIndirizzo), TipoIndirizzoResponse, "Tipo indirizzo"
    )


@router.get("/", response_model=PagedResponse[TipoIndirizzoResponse])
async def list_tipi_indirizzo(
    params: PageParams = Depends(),
    service: LookupService[TipoIndirizzoResponse] = Depends(get_service),
) -> PagedResponse[TipoIndirizzoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=TipoIndirizzoResponse)
async def get_tipo_indirizzo(
    codice: int,
    service: LookupService[TipoIndirizzoResponse] = Depends(get_service),
) -> TipoIndirizzoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=TipoIndirizzoResponse, status_code=status.HTTP_201_CREATED
)
async def create_tipo_indirizzo(
    data: TipoIndirizzoCreate,
    service: LookupService[TipoIndirizzoResponse] = Depends(get_service),
) -> TipoIndirizzoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=TipoIndirizzoResponse)
async def update_tipo_indirizzo(
    codice: int,
    data: TipoIndirizzoUpdate,
    service: LookupService[TipoIndirizzoResponse] = Depends(get_service),
) -> TipoIndirizzoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tipo_indirizzo(
    codice: int,
    service: LookupService[TipoIndirizzoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
