from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import TipoSpartito
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    TipoSpartitoCreate,
    TipoSpartitoResponse,
    TipoSpartitoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/tipi-spartito", tags=["tipi-spartito"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[TipoSpartitoResponse]:
    return LookupService(
        LookupRepository(db, TipoSpartito), TipoSpartitoResponse, "Tipo spartito"
    )


@router.get("/", response_model=PagedResponse[TipoSpartitoResponse])
async def list_tipi_spartito(
    params: PageParams = Depends(),
    service: LookupService[TipoSpartitoResponse] = Depends(get_service),
) -> PagedResponse[TipoSpartitoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=TipoSpartitoResponse)
async def get_tipo_spartito(
    codice: int, service: LookupService[TipoSpartitoResponse] = Depends(get_service)
) -> TipoSpartitoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=TipoSpartitoResponse, status_code=status.HTTP_201_CREATED
)
async def create_tipo_spartito(
    data: TipoSpartitoCreate,
    service: LookupService[TipoSpartitoResponse] = Depends(get_service),
) -> TipoSpartitoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=TipoSpartitoResponse)
async def update_tipo_spartito(
    codice: int,
    data: TipoSpartitoUpdate,
    service: LookupService[TipoSpartitoResponse] = Depends(get_service),
) -> TipoSpartitoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tipo_spartito(
    codice: int, service: LookupService[TipoSpartitoResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
