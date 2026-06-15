from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.contatto import ContattoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.contatto_repository import ContattoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.contatto import ContattoCreate, ContattoResponse, ContattoUpdate
from app.services.contatto_service import ContattoService

router = APIRouter(prefix="/contatti", tags=["contatti"])


def get_service(db: AsyncSession = Depends(get_db)) -> ContattoService:
    return ContattoService(ContattoRepository(db), PersonaRepository(db))


@router.get("/persona/{persona_id}", response_model=PagedResponse[ContattoResponse])
async def get_contatti_persona(
    persona_id: int,
    params: PageParams = Depends(),
    service: ContattoService = Depends(get_service),
) -> PagedResponse[ContattoResponse]:
    try:
        return await service.get_by_persona(persona_id, params)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{contatto_id}", response_model=ContattoResponse)
async def get_contatto(
    contatto_id: int, service: ContattoService = Depends(get_service)
) -> ContattoResponse:
    try:
        return await service.get_by_id(contatto_id)
    except ContattoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=ContattoResponse, status_code=status.HTTP_201_CREATED)
async def create_contatto(
    data: ContattoCreate, service: ContattoService = Depends(get_service)
) -> ContattoResponse:
    try:
        return await service.create(data)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{contatto_id}", response_model=ContattoResponse)
async def update_contatto(
    contatto_id: int,
    data: ContattoUpdate,
    service: ContattoService = Depends(get_service),
) -> ContattoResponse:
    try:
        return await service.update(contatto_id, data)
    except ContattoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{contatto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contatto(
    contatto_id: int, service: ContattoService = Depends(get_service)
) -> None:
    try:
        await service.delete(contatto_id)
    except ContattoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
