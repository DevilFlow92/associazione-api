from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.spartito import NomeParteNotFoundError
from app.repositories.nome_parte_repository import NomeParteRepository
from app.schemas.spartito import NomeParteCreate, NomeParteResponse, NomeParteUpdate
from app.services.nome_parte_service import NomeParteService

router = APIRouter(prefix="/nome-parti", tags=["nome-parti"])


def get_service(db: AsyncSession = Depends(get_db)) -> NomeParteService:
    return NomeParteService(NomeParteRepository(db))


@router.get("/", response_model=PagedResponse[NomeParteResponse])
async def list_nome_parti(
    banda_codice: int,
    tipo_spartito_codice: int | None = Query(None),
    params: PageParams = Depends(),
    service: NomeParteService = Depends(get_service),
) -> PagedResponse[NomeParteResponse]:
    return await service.get_all(banda_codice, tipo_spartito_codice, params)


@router.get("/{id}", response_model=NomeParteResponse)
async def get_nome_parte(
    id: int,
    service: NomeParteService = Depends(get_service),
) -> NomeParteResponse:
    try:
        return await service.get_by_id(id)
    except NomeParteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=NomeParteResponse, status_code=status.HTTP_201_CREATED)
async def create_nome_parte(
    data: NomeParteCreate,
    service: NomeParteService = Depends(get_service),
) -> NomeParteResponse:
    return await service.create(data)


@router.patch("/{id}", response_model=NomeParteResponse)
async def update_nome_parte(
    id: int,
    data: NomeParteUpdate,
    service: NomeParteService = Depends(get_service),
) -> NomeParteResponse:
    try:
        return await service.update(id, data)
    except NomeParteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nome_parte(
    id: int,
    service: NomeParteService = Depends(get_service),
) -> None:
    try:
        await service.delete(id)
    except NomeParteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
