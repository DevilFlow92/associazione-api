from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.presenza import PresenzaNotFoundError
from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.persona_repository import PersonaRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.presenza import PresenzaCreate, PresenzaResponse, PresenzaUpdate
from app.services.presenza_service import PresenzaService

router = APIRouter(prefix="/presenze", tags=["presenze"])


def get_service(db: AsyncSession = Depends(get_db)) -> PresenzaService:
    return PresenzaService(
        PresenzaRepository(db),
        PersonaRepository(db),
        ServizioRepository(db),
        ProvaRepository(db),
    )


@router.get("/servizio/{servizio_id}", response_model=PagedResponse[PresenzaResponse])
async def get_organico_servizio(
    servizio_id: int,
    params: PageParams = Depends(),
    service: PresenzaService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_by_servizio(servizio_id, params)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/prova/{prova_id}", response_model=PagedResponse[PresenzaResponse])
async def get_organico_prova(
    prova_id: int,
    params: PageParams = Depends(),
    service: PresenzaService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_by_prova(prova_id, params)
    except ProvaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{presenza_id}", response_model=PresenzaResponse)
async def get_presenza(
    presenza_id: int, service: PresenzaService = Depends(get_service)
) -> PresenzaResponse:
    try:
        return await service.get_by_id(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=PresenzaResponse, status_code=status.HTTP_201_CREATED)
async def create_presenza(
    data: PresenzaCreate, service: PresenzaService = Depends(get_service)
) -> PresenzaResponse:
    try:
        return await service.create(data)
    except (PersonaNotFoundError, ServizioNotFoundError, ProvaNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{presenza_id}", response_model=PresenzaResponse)
async def update_presenza(
    presenza_id: int,
    data: PresenzaUpdate,
    service: PresenzaService = Depends(get_service),
) -> PresenzaResponse:
    try:
        return await service.update(presenza_id, data)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{presenza_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_presenza(
    presenza_id: int, service: PresenzaService = Depends(get_service)
) -> None:
    try:
        await service.delete(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
