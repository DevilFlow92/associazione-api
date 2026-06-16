from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.voce_contabilita import (
    VoceContabilitaHasFlussiError,
    VoceContabilitaNotFoundError,
)
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.voce_contabilita import (
    VoceContabilitaCreate,
    VoceContabilitaResponse,
    VoceContabilitaUpdate,
)
from app.services.voce_contabilita_service import VoceContabilitaService

router = APIRouter(prefix="/voci-contabilita", tags=["voci-contabilita"])


def get_service(db: AsyncSession = Depends(get_db)) -> VoceContabilitaService:
    return VoceContabilitaService(VoceContabilitaRepository(db))


@router.get("/", response_model=PagedResponse[VoceContabilitaResponse])
async def list_voci_contabilita(
    banda_codice: int | None = None,
    params: PageParams = Depends(),
    service: VoceContabilitaService = Depends(get_service),
) -> PagedResponse[VoceContabilitaResponse]:
    return await service.get_all(banda_codice, params)


@router.get("/{voce_id}", response_model=VoceContabilitaResponse)
async def get_voce_contabilita(
    voce_id: int, service: VoceContabilitaService = Depends(get_service)
) -> VoceContabilitaResponse:
    try:
        return await service.get_by_id(voce_id)
    except VoceContabilitaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/", response_model=VoceContabilitaResponse, status_code=status.HTTP_201_CREATED
)
async def create_voce_contabilita(
    data: VoceContabilitaCreate,
    service: VoceContabilitaService = Depends(get_service),
) -> VoceContabilitaResponse:
    return await service.create(data)


@router.patch("/{voce_id}", response_model=VoceContabilitaResponse)
async def update_voce_contabilita(
    voce_id: int,
    data: VoceContabilitaUpdate,
    service: VoceContabilitaService = Depends(get_service),
) -> VoceContabilitaResponse:
    try:
        return await service.update(voce_id, data)
    except VoceContabilitaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{voce_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_voce_contabilita(
    voce_id: int, service: VoceContabilitaService = Depends(get_service)
) -> None:
    try:
        await service.delete(voce_id)
    except VoceContabilitaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except VoceContabilitaHasFlussiError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
