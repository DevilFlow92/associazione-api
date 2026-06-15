from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Stato
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import StatoCreate, StatoResponse, StatoUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/stati", tags=["stati"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[StatoResponse]:
    return LookupService(LookupRepository(db, Stato), StatoResponse, "Stato")


@router.get("/", response_model=PagedResponse[StatoResponse])
async def list_stati(
    params: PageParams = Depends(),
    service: LookupService[StatoResponse] = Depends(get_service),
) -> PagedResponse[StatoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=StatoResponse)
async def get_stato(
    codice: int, service: LookupService[StatoResponse] = Depends(get_service)
) -> StatoResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=StatoResponse, status_code=status.HTTP_201_CREATED)
async def create_stato(
    data: StatoCreate, service: LookupService[StatoResponse] = Depends(get_service)
) -> StatoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=StatoResponse)
async def update_stato(
    codice: int,
    data: StatoUpdate,
    service: LookupService[StatoResponse] = Depends(get_service),
) -> StatoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_stato(
    codice: int, service: LookupService[StatoResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
