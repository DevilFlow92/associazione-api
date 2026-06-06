from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.iscrizione import (
    IscrizioneDuplicataError,
    IscrizioneNotFoundError,
)
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


@router.get("/socio/{socio_id}", response_model=list[IscrizioneResponse])
async def get_iscrizioni_socio(
    socio_id: int, service: IscrizioneService = Depends(get_service)
) -> list[IscrizioneResponse]:
    try:
        return await service.get_by_socio(socio_id)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{iscrizione_id}", response_model=IscrizioneResponse)
async def get_iscrizione(
    iscrizione_id: int, service: IscrizioneService = Depends(get_service)
) -> IscrizioneResponse:
    try:
        return await service.get_by_id(iscrizione_id)
    except IscrizioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=IscrizioneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_iscrizione(
    data: IscrizioneCreate, service: IscrizioneService = Depends(get_service)
) -> IscrizioneResponse:
    try:
        return await service.create(data)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except IscrizioneDuplicataError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


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
