from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import VoceRendiconto
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    VoceRendicontoCreate,
    VoceRendicontoResponse,
    VoceRendicontoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/voci-rendiconto", tags=["voci-rendiconto"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[VoceRendicontoResponse]:
    return LookupService(
        LookupRepository(db, VoceRendiconto),
        VoceRendicontoResponse,
        "Voce rendiconto",
    )


@router.get("/", response_model=PagedResponse[VoceRendicontoResponse])
async def list_voci_rendiconto(
    params: PageParams = Depends(),
    sezione_codice: int | None = Query(None),
    service: LookupService[VoceRendicontoResponse] = Depends(get_service),
) -> PagedResponse[VoceRendicontoResponse]:
    filters = {"sezione_codice": sezione_codice} if sezione_codice is not None else None
    return await service.get_all(params, filters=filters)


@router.get("/{codice}", response_model=VoceRendicontoResponse)
async def get_voce_rendiconto(
    codice: int,
    service: LookupService[VoceRendicontoResponse] = Depends(get_service),
) -> VoceRendicontoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=VoceRendicontoResponse, status_code=status.HTTP_201_CREATED
)
async def create_voce_rendiconto(
    data: VoceRendicontoCreate,
    service: LookupService[VoceRendicontoResponse] = Depends(get_service),
) -> VoceRendicontoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=VoceRendicontoResponse)
async def update_voce_rendiconto(
    codice: int,
    data: VoceRendicontoUpdate,
    service: LookupService[VoceRendicontoResponse] = Depends(get_service),
) -> VoceRendicontoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voce_rendiconto(
    codice: int,
    service: LookupService[VoceRendicontoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
