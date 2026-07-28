from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.models.lookups import TipoCorso
from app.repositories.corso_repository import CorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.corso import CorsoCreate, CorsoResponse, CorsoUpdate
from app.services.corso_service import CorsoService

router = APIRouter(prefix="/corsi", tags=["corsi"])


def get_service(db: AsyncSession = Depends(get_db)) -> CorsoService:
    return CorsoService(
        CorsoRepository(db), LookupRepository(db, TipoCorso), PersonaRepository(db)
    )


@router.get(
    "/",
    response_model=PagedResponse[CorsoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_corsi(
    banda_codice: int | None = Query(None),
    anno: int | None = Query(None),
    tipo_corso_codice: int | None = Query(None),
    params: PageParams = Depends(),
    service: CorsoService = Depends(get_service),
) -> PagedResponse[CorsoResponse]:
    return await service.get_all(
        params,
        banda_codice=banda_codice,
        anno=anno,
        tipo_corso_codice=tipo_corso_codice,
    )


@router.get(
    "/{corso_id}",
    response_model=CorsoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_corso(
    corso_id: int, service: CorsoService = Depends(get_service)
) -> CorsoResponse:
    try:
        return await service.get_by_id(corso_id)
    except CorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=CorsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_corso(
    data: CorsoCreate, service: CorsoService = Depends(get_service)
) -> CorsoResponse:
    try:
        return await service.create(data)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{corso_id}",
    response_model=CorsoResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_corso(
    corso_id: int,
    data: CorsoUpdate,
    service: CorsoService = Depends(get_service),
) -> CorsoResponse:
    try:
        return await service.update(corso_id, data)
    except (CorsoNotFoundError, PersonaNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{corso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def delete_corso(
    corso_id: int, service: CorsoService = Depends(get_service)
) -> None:
    try:
        await service.delete(corso_id)
    except CorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
