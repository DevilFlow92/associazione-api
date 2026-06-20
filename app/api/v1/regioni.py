from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Regione
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import RegioneCreate, RegioneResponse, RegioneUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/regioni", tags=["regioni"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[RegioneResponse]:
    return LookupService(LookupRepository(db, Regione), RegioneResponse, "Regione")


@router.get("/", response_model=PagedResponse[RegioneResponse])
async def list_regioni(
    params: PageParams = Depends(),
    stato_codice: int | None = Query(None),
    service: LookupService[RegioneResponse] = Depends(get_service),
) -> PagedResponse[RegioneResponse]:
    filters = {"stato_codice": stato_codice} if stato_codice is not None else None
    return await service.get_all(params, filters=filters)


@router.get("/{codice}", response_model=RegioneResponse)
async def get_regione(
    codice: int, service: LookupService[RegioneResponse] = Depends(get_service)
) -> RegioneResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=RegioneResponse, status_code=status.HTTP_201_CREATED)
async def create_regione(
    data: RegioneCreate, service: LookupService[RegioneResponse] = Depends(get_service)
) -> RegioneResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=RegioneResponse)
async def update_regione(
    codice: int,
    data: RegioneUpdate,
    service: LookupService[RegioneResponse] = Depends(get_service),
) -> RegioneResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_regione(
    codice: int, service: LookupService[RegioneResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
