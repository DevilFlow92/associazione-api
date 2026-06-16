from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.iscrizione import IscrizioneNotFoundError
from app.exceptions.socio import SocioNotFoundError
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.iscrizione import (
    IscrizioneCreate,
    IscrizioneResponse,
    IscrizioneUpdate,
)
from app.services.iscrizione_service import IscrizioneService

router = APIRouter(prefix="/iscrizioni", tags=["iscrizioni"])


def get_service(db: AsyncSession = Depends(get_db)) -> IscrizioneService:
    return IscrizioneService(IscrizioneRepository(db), SocioRepository(db))


@router.get("/", response_model=PagedResponse[IscrizioneResponse])
async def list_iscrizioni(
    socio_id: int | None = Query(None),
    anno: int | None = Query(None),
    params: PageParams = Depends(),
    service: IscrizioneService = Depends(get_service),
) -> PagedResponse[IscrizioneResponse]:
    return await service.get_all(socio_id, anno, params)


@router.get("/{iscrizione_id}", response_model=IscrizioneResponse)
async def get_iscrizione(
    iscrizione_id: int, service: IscrizioneService = Depends(get_service)
) -> IscrizioneResponse:
    try:
        return await service.get_by_id(iscrizione_id)
    except IscrizioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/", response_model=IscrizioneResponse, status_code=status.HTTP_201_CREATED
)
async def create_iscrizione(
    data: IscrizioneCreate, service: IscrizioneService = Depends(get_service)
) -> IscrizioneResponse:
    try:
        return await service.create(data)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{iscrizione_id}", response_model=IscrizioneResponse)
async def update_iscrizione(
    iscrizione_id: int,
    data: IscrizioneUpdate,
    service: IscrizioneService = Depends(get_service),
) -> IscrizioneResponse:
    try:
        return await service.update(iscrizione_id, data)
    except IscrizioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{iscrizione_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_iscrizione(
    iscrizione_id: int, service: IscrizioneService = Depends(get_service)
) -> None:
    try:
        await service.delete(iscrizione_id)
    except IscrizioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
