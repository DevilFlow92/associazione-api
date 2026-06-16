from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.servizio import ServizioHasRicevuteError, ServizioNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.servizio import ServizioCreate, ServizioResponse, ServizioUpdate
from app.services.servizio_service import ServizioService

router = APIRouter(prefix="/servizi", tags=["servizi"])


def get_service(db: AsyncSession = Depends(get_db)) -> ServizioService:
    return ServizioService(ServizioRepository(db), IndirizzoRepository(db))


@router.get("/", response_model=PagedResponse[ServizioResponse])
async def list_servizi(
    anno: int | None = None,
    params: PageParams = Depends(),
    service: ServizioService = Depends(get_service),
) -> PagedResponse[ServizioResponse]:
    return await service.get_all(anno, params)


@router.get("/{servizio_id}", response_model=ServizioResponse)
async def get_servizio(
    servizio_id: int, service: ServizioService = Depends(get_service)
) -> ServizioResponse:
    try:
        return await service.get_by_id(servizio_id)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=ServizioResponse, status_code=status.HTTP_201_CREATED)
async def create_servizio(
    data: ServizioCreate, service: ServizioService = Depends(get_service)
) -> ServizioResponse:
    try:
        return await service.create(data)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{servizio_id}", response_model=ServizioResponse)
async def update_servizio(
    servizio_id: int,
    data: ServizioUpdate,
    service: ServizioService = Depends(get_service),
) -> ServizioResponse:
    try:
        return await service.update(servizio_id, data)
    except (ServizioNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{servizio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_servizio(
    servizio_id: int, service: ServizioService = Depends(get_service)
) -> None:
    try:
        await service.delete(servizio_id)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ServizioHasRicevuteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
