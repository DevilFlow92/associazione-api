from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import RuoloBanda
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import RuoloBandaCreate, RuoloBandaResponse, RuoloBandaUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/ruoli-banda", tags=["ruoli-banda"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[RuoloBandaResponse]:
    return LookupService(
        LookupRepository(db, RuoloBanda), RuoloBandaResponse, "Ruolo banda"
    )


@router.get("/", response_model=PagedResponse[RuoloBandaResponse])
async def list_ruoli_banda(
    params: PageParams = Depends(),
    service: LookupService[RuoloBandaResponse] = Depends(get_service),
) -> PagedResponse[RuoloBandaResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=RuoloBandaResponse)
async def get_ruolo_banda(
    codice: int,
    service: LookupService[RuoloBandaResponse] = Depends(get_service),
) -> RuoloBandaResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=RuoloBandaResponse, status_code=status.HTTP_201_CREATED
)
async def create_ruolo_banda(
    data: RuoloBandaCreate,
    service: LookupService[RuoloBandaResponse] = Depends(get_service),
) -> RuoloBandaResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=RuoloBandaResponse)
async def update_ruolo_banda(
    codice: int,
    data: RuoloBandaUpdate,
    service: LookupService[RuoloBandaResponse] = Depends(get_service),
) -> RuoloBandaResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ruolo_banda(
    codice: int,
    service: LookupService[RuoloBandaResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
