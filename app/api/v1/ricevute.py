from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.esterno import EsternoNotFoundError
from app.exceptions.ricevuta import RicevutaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.esterno_repository import EsternoRepository
from app.repositories.ricevuta_repository import RicevutaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.ricevuta import RicevutaCreate, RicevutaResponse, RicevutaUpdate
from app.services.ricevuta_service import RicevutaService

router = APIRouter(prefix="/ricevute", tags=["ricevute"])


def get_service(db: AsyncSession = Depends(get_db)) -> RicevutaService:
    return RicevutaService(
        RicevutaRepository(db), ServizioRepository(db), EsternoRepository(db)
    )


@router.get("/", response_model=PagedResponse[RicevutaResponse])
async def list_ricevute(
    params: PageParams = Depends(),
    service: RicevutaService = Depends(get_service),
) -> PagedResponse[RicevutaResponse]:
    return await service.get_all(params)


@router.get("/servizio/{servizio_id}", response_model=PagedResponse[RicevutaResponse])
async def get_ricevute_servizio(
    servizio_id: int,
    params: PageParams = Depends(),
    service: RicevutaService = Depends(get_service),
) -> PagedResponse[RicevutaResponse]:
    try:
        return await service.get_by_servizio(servizio_id, params)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{ricevuta_id}", response_model=RicevutaResponse)
async def get_ricevuta(
    ricevuta_id: int, service: RicevutaService = Depends(get_service)
) -> RicevutaResponse:
    try:
        return await service.get_by_id(ricevuta_id)
    except RicevutaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=RicevutaResponse, status_code=status.HTTP_201_CREATED)
async def create_ricevuta(
    data: RicevutaCreate, service: RicevutaService = Depends(get_service)
) -> RicevutaResponse:
    try:
        return await service.create(data)
    except (ServizioNotFoundError, EsternoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{ricevuta_id}", response_model=RicevutaResponse)
async def update_ricevuta(
    ricevuta_id: int,
    data: RicevutaUpdate,
    service: RicevutaService = Depends(get_service),
) -> RicevutaResponse:
    try:
        return await service.update(ricevuta_id, data)
    except RicevutaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{ricevuta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ricevuta(
    ricevuta_id: int, service: RicevutaService = Depends(get_service)
) -> None:
    try:
        await service.delete(ricevuta_id)
    except RicevutaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
