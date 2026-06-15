from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Banda
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import BandaCreate, BandaResponse, BandaUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/bande", tags=["bande"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[BandaResponse]:
    return LookupService(LookupRepository(db, Banda), BandaResponse, "Banda")


@router.get("/", response_model=PagedResponse[BandaResponse])
async def list_bande(
    params: PageParams = Depends(),
    service: LookupService[BandaResponse] = Depends(get_service),
) -> PagedResponse[BandaResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=BandaResponse)
async def get_banda(
    codice: int, service: LookupService[BandaResponse] = Depends(get_service)
) -> BandaResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=BandaResponse, status_code=status.HTTP_201_CREATED)
async def create_banda(
    data: BandaCreate, service: LookupService[BandaResponse] = Depends(get_service)
) -> BandaResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=BandaResponse)
async def update_banda(
    codice: int,
    data: BandaUpdate,
    service: LookupService[BandaResponse] = Depends(get_service),
) -> BandaResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banda(
    codice: int, service: LookupService[BandaResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
