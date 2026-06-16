from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.flusso_cassa import FlussoCassaNotFoundError
from app.exceptions.voce_contabilita import VoceContabilitaNotFoundError
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.flusso_cassa import (
    FlussoCassaCreate,
    FlussoCassaResponse,
    FlussoCassaUpdate,
)
from app.services.flusso_cassa_service import FlussoCassaService

router = APIRouter(prefix="/flussi-cassa", tags=["flussi-cassa"])


def get_service(db: AsyncSession = Depends(get_db)) -> FlussoCassaService:
    return FlussoCassaService(FlussoCassaRepository(db), VoceContabilitaRepository(db))


@router.get("/", response_model=PagedResponse[FlussoCassaResponse])
async def list_flussi_cassa(
    params: PageParams = Depends(),
    service: FlussoCassaService = Depends(get_service),
) -> PagedResponse[FlussoCassaResponse]:
    return await service.get_all(params)


@router.get(
    "/voce-contabilita/{voce_contabilita_id}",
    response_model=PagedResponse[FlussoCassaResponse],
)
async def get_flussi_voce_contabilita(
    voce_contabilita_id: int,
    params: PageParams = Depends(),
    service: FlussoCassaService = Depends(get_service),
) -> PagedResponse[FlussoCassaResponse]:
    try:
        return await service.get_by_voce(voce_contabilita_id, params)
    except VoceContabilitaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{flusso_id}", response_model=FlussoCassaResponse)
async def get_flusso_cassa(
    flusso_id: int, service: FlussoCassaService = Depends(get_service)
) -> FlussoCassaResponse:
    try:
        return await service.get_by_id(flusso_id)
    except FlussoCassaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/", response_model=FlussoCassaResponse, status_code=status.HTTP_201_CREATED
)
async def create_flusso_cassa(
    data: FlussoCassaCreate, service: FlussoCassaService = Depends(get_service)
) -> FlussoCassaResponse:
    try:
        return await service.create(data)
    except VoceContabilitaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{flusso_id}", response_model=FlussoCassaResponse)
async def update_flusso_cassa(
    flusso_id: int,
    data: FlussoCassaUpdate,
    service: FlussoCassaService = Depends(get_service),
) -> FlussoCassaResponse:
    try:
        return await service.update(flusso_id, data)
    except FlussoCassaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{flusso_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_flusso_cassa(
    flusso_id: int, service: FlussoCassaService = Depends(get_service)
) -> None:
    try:
        await service.delete(flusso_id)
    except FlussoCassaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
