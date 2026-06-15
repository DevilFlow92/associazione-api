from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import RuoloContatto
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    RuoloContattoCreate,
    RuoloContattoResponse,
    RuoloContattoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/ruoli-contatto", tags=["ruoli-contatto"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[RuoloContattoResponse]:
    return LookupService(
        LookupRepository(db, RuoloContatto), RuoloContattoResponse, "Ruolo contatto"
    )


@router.get("/", response_model=PagedResponse[RuoloContattoResponse])
async def list_ruoli_contatto(
    params: PageParams = Depends(),
    service: LookupService[RuoloContattoResponse] = Depends(get_service),
) -> PagedResponse[RuoloContattoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=RuoloContattoResponse)
async def get_ruolo_contatto(
    codice: int,
    service: LookupService[RuoloContattoResponse] = Depends(get_service),
) -> RuoloContattoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=RuoloContattoResponse, status_code=status.HTTP_201_CREATED
)
async def create_ruolo_contatto(
    data: RuoloContattoCreate,
    service: LookupService[RuoloContattoResponse] = Depends(get_service),
) -> RuoloContattoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=RuoloContattoResponse)
async def update_ruolo_contatto(
    codice: int,
    data: RuoloContattoUpdate,
    service: LookupService[RuoloContattoResponse] = Depends(get_service),
) -> RuoloContattoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ruolo_contatto(
    codice: int,
    service: LookupService[RuoloContattoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
