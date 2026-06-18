from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.esterno import EsternoDuplicateCodiceError, EsternoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.esterno_repository import EsternoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.esterno import EsternoCreate, EsternoResponse, EsternoUpdate
from app.services.esterno_service import EsternoService

router = APIRouter(prefix="/esterni", tags=["esterni"])


def get_service(db: AsyncSession = Depends(get_db)) -> EsternoService:
    return EsternoService(EsternoRepository(db), PersonaRepository(db))


@router.get("/", response_model=PagedResponse[EsternoResponse])
async def list_esterni(
    banda_codice: int | None = Query(None),
    params: PageParams = Depends(),
    service: EsternoService = Depends(get_service),
) -> PagedResponse[EsternoResponse]:
    return await service.get_all(params, banda_codice=banda_codice)


@router.get("/{esterno_id}", response_model=EsternoResponse)
async def get_esterno(
    esterno_id: int, service: EsternoService = Depends(get_service)
) -> EsternoResponse:
    try:
        return await service.get_by_id(esterno_id)
    except EsternoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=EsternoResponse, status_code=status.HTTP_201_CREATED)
async def create_esterno(
    data: EsternoCreate, service: EsternoService = Depends(get_service)
) -> EsternoResponse:
    try:
        return await service.create(data)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EsternoDuplicateCodiceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{esterno_id}", response_model=EsternoResponse)
async def update_esterno(
    esterno_id: int,
    data: EsternoUpdate,
    service: EsternoService = Depends(get_service),
) -> EsternoResponse:
    try:
        return await service.update(esterno_id, data)
    except EsternoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except EsternoDuplicateCodiceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{esterno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_esterno(
    esterno_id: int, service: EsternoService = Depends(get_service)
) -> None:
    try:
        await service.delete(esterno_id)
    except EsternoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
