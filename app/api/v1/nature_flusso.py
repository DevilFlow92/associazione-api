from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import NaturaFlusso
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    NaturaFlussoCreate,
    NaturaFlussoResponse,
    NaturaFlussoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/nature-flusso", tags=["nature-flusso"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[NaturaFlussoResponse]:
    return LookupService(
        LookupRepository(db, NaturaFlusso), NaturaFlussoResponse, "Natura flusso"
    )


@router.get("/", response_model=PagedResponse[NaturaFlussoResponse])
async def list_nature_flusso(
    params: PageParams = Depends(),
    service: LookupService[NaturaFlussoResponse] = Depends(get_service),
) -> PagedResponse[NaturaFlussoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=NaturaFlussoResponse)
async def get_natura_flusso(
    codice: int,
    service: LookupService[NaturaFlussoResponse] = Depends(get_service),
) -> NaturaFlussoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/", response_model=NaturaFlussoResponse, status_code=status.HTTP_201_CREATED
)
async def create_natura_flusso(
    data: NaturaFlussoCreate,
    service: LookupService[NaturaFlussoResponse] = Depends(get_service),
) -> NaturaFlussoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=NaturaFlussoResponse)
async def update_natura_flusso(
    codice: int,
    data: NaturaFlussoUpdate,
    service: LookupService[NaturaFlussoResponse] = Depends(get_service),
) -> NaturaFlussoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_natura_flusso(
    codice: int,
    service: LookupService[NaturaFlussoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
