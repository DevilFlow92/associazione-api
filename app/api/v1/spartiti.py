from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.spartito import SpartitoNotFoundError
from app.repositories.spartito_repository import SpartitoRepository
from app.schemas.spartito import SpartitoCreate, SpartitoResponse, SpartitoUpdate
from app.services.spartito_service import SpartitoService

router = APIRouter(prefix="/spartiti", tags=["spartiti"])


def get_service(db: AsyncSession = Depends(get_db)) -> SpartitoService:
    return SpartitoService(SpartitoRepository(db))


@router.get("/", response_model=PagedResponse[SpartitoResponse])
async def list_spartiti(
    tipo_spartito_codice: int | None = Query(None),
    strumento_codice: int | None = Query(None),
    banda_codice: int | None = Query(None),
    nome_parte_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: SpartitoService = Depends(get_service),
) -> PagedResponse[SpartitoResponse]:
    return await service.get_all(
        tipo_spartito_codice,
        strumento_codice,
        params,
        banda_codice=banda_codice,
        nome_parte_id=nome_parte_id,
    )


@router.get("/{spartito_id}", response_model=SpartitoResponse)
async def get_spartito(
    spartito_id: int, service: SpartitoService = Depends(get_service)
) -> SpartitoResponse:
    try:
        return await service.get_by_id(spartito_id)
    except SpartitoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=SpartitoResponse, status_code=status.HTTP_201_CREATED)
async def create_spartito(
    data: SpartitoCreate, service: SpartitoService = Depends(get_service)
) -> SpartitoResponse:
    return await service.create(data)


@router.patch("/{spartito_id}", response_model=SpartitoResponse)
async def update_spartito(
    spartito_id: int,
    data: SpartitoUpdate,
    service: SpartitoService = Depends(get_service),
) -> SpartitoResponse:
    try:
        return await service.update(spartito_id, data)
    except SpartitoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{spartito_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_spartito(
    spartito_id: int, service: SpartitoService = Depends(get_service)
) -> None:
    try:
        await service.delete(spartito_id)
    except SpartitoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
