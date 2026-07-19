from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.repertorio_item import RepertorioItemNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.exceptions.spartito import NomeParteNotFoundError
from app.repositories.nome_parte_repository import NomeParteRepository
from app.repositories.repertorio_item_repository import RepertorioItemRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.repertorio_item import (
    RepertorioItemCreate,
    RepertorioItemResponse,
    RepertorioItemUpdate,
)
from app.services.repertorio_item_service import RepertorioItemService

router = APIRouter(prefix="/repertorio", tags=["repertorio"])


def get_service(db: AsyncSession = Depends(get_db)) -> RepertorioItemService:
    return RepertorioItemService(
        RepertorioItemRepository(db), NomeParteRepository(db), ServizioRepository(db)
    )


@router.get(
    "/servizio/{servizio_id}", response_model=PagedResponse[RepertorioItemResponse]
)
async def get_repertorio_servizio(
    servizio_id: int,
    params: PageParams = Depends(),
    service: RepertorioItemService = Depends(get_service),
) -> PagedResponse[RepertorioItemResponse]:
    try:
        return await service.get_by_servizio(servizio_id, params)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{repertorio_item_id}", response_model=RepertorioItemResponse)
async def get_repertorio_item(
    repertorio_item_id: int, service: RepertorioItemService = Depends(get_service)
) -> RepertorioItemResponse:
    try:
        return await service.get_by_id(repertorio_item_id)
    except RepertorioItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/", response_model=RepertorioItemResponse, status_code=status.HTTP_201_CREATED
)
async def create_repertorio_item(
    data: RepertorioItemCreate, service: RepertorioItemService = Depends(get_service)
) -> RepertorioItemResponse:
    try:
        return await service.create(data)
    except (NomeParteNotFoundError, ServizioNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{repertorio_item_id}", response_model=RepertorioItemResponse)
async def update_repertorio_item(
    repertorio_item_id: int,
    data: RepertorioItemUpdate,
    service: RepertorioItemService = Depends(get_service),
) -> RepertorioItemResponse:
    try:
        return await service.update(repertorio_item_id, data)
    except RepertorioItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{repertorio_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repertorio_item(
    repertorio_item_id: int, service: RepertorioItemService = Depends(get_service)
) -> None:
    try:
        await service.delete(repertorio_item_id)
    except RepertorioItemNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
