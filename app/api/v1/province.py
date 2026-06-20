from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Provincia
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import ProvinciaCreate, ProvinciaResponse, ProvinciaUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/province", tags=["province"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[ProvinciaResponse]:
    return LookupService(
        LookupRepository(db, Provincia), ProvinciaResponse, "Provincia"
    )


@router.get("/", response_model=PagedResponse[ProvinciaResponse])
async def list_province(
    params: PageParams = Depends(),
    regione_codice: int | None = Query(None),
    service: LookupService[ProvinciaResponse] = Depends(get_service),
) -> PagedResponse[ProvinciaResponse]:
    filters = {"regione_codice": regione_codice} if regione_codice is not None else None
    return await service.get_all(params, filters=filters)


@router.get("/{codice}", response_model=ProvinciaResponse)
async def get_provincia(
    codice: int, service: LookupService[ProvinciaResponse] = Depends(get_service)
) -> ProvinciaResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=ProvinciaResponse, status_code=status.HTTP_201_CREATED)
async def create_provincia(
    data: ProvinciaCreate,
    service: LookupService[ProvinciaResponse] = Depends(get_service),
) -> ProvinciaResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=ProvinciaResponse)
async def update_provincia(
    codice: int,
    data: ProvinciaUpdate,
    service: LookupService[ProvinciaResponse] = Depends(get_service),
) -> ProvinciaResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provincia(
    codice: int, service: LookupService[ProvinciaResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
