from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Comune
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import ComuneCreate, ComuneResponse, ComuneUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/comuni", tags=["comuni"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[ComuneResponse]:
    return LookupService(LookupRepository(db, Comune), ComuneResponse, "Comune")


@router.get("/", response_model=PagedResponse[ComuneResponse])
async def list_comuni(
    params: PageParams = Depends(),
    service: LookupService[ComuneResponse] = Depends(get_service),
) -> PagedResponse[ComuneResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=ComuneResponse)
async def get_comune(
    codice: int, service: LookupService[ComuneResponse] = Depends(get_service)
) -> ComuneResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=ComuneResponse, status_code=status.HTTP_201_CREATED)
async def create_comune(
    data: ComuneCreate, service: LookupService[ComuneResponse] = Depends(get_service)
) -> ComuneResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=ComuneResponse)
async def update_comune(
    codice: int,
    data: ComuneUpdate,
    service: LookupService[ComuneResponse] = Depends(get_service),
) -> ComuneResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comune(
    codice: int, service: LookupService[ComuneResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
