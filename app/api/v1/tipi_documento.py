from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import TipoDocumento
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    TipoDocumentoCreate,
    TipoDocumentoResponse,
    TipoDocumentoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/tipi-documento", tags=["tipi-documento"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[TipoDocumentoResponse]:
    return LookupService(
        LookupRepository(db, TipoDocumento), TipoDocumentoResponse, "Tipo documento"
    )


@router.get("/", response_model=PagedResponse[TipoDocumentoResponse])
async def list_tipi_documento(
    params: PageParams = Depends(),
    service: LookupService[TipoDocumentoResponse] = Depends(get_service),
) -> PagedResponse[TipoDocumentoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=TipoDocumentoResponse)
async def get_tipo_documento(
    codice: int, service: LookupService[TipoDocumentoResponse] = Depends(get_service)
) -> TipoDocumentoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=TipoDocumentoResponse, status_code=status.HTTP_201_CREATED
)
async def create_tipo_documento(
    data: TipoDocumentoCreate,
    service: LookupService[TipoDocumentoResponse] = Depends(get_service),
) -> TipoDocumentoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=TipoDocumentoResponse)
async def update_tipo_documento(
    codice: int,
    data: TipoDocumentoUpdate,
    service: LookupService[TipoDocumentoResponse] = Depends(get_service),
) -> TipoDocumentoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tipo_documento(
    codice: int, service: LookupService[TipoDocumentoResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
