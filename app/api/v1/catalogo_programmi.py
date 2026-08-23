from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.lookup import LookupNotFoundError
from app.exceptions.voce_programma_catalogo import (
    VoceProgrammaCatalogoDuplicataError,
    VoceProgrammaCatalogoNotFoundError,
)
from app.models.lookups import TipoCorso
from app.repositories.lookup import LookupRepository
from app.repositories.voce_programma_catalogo_repository import (
    VoceProgrammaCatalogoRepository,
)
from app.schemas.voce_programma_catalogo import (
    VoceProgrammaCatalogoCreate,
    VoceProgrammaCatalogoResponse,
    VoceProgrammaCatalogoUpdate,
)
from app.services.voce_programma_catalogo_service import VoceProgrammaCatalogoService

router = APIRouter(prefix="/catalogo-programmi", tags=["catalogo-programmi"])


def get_service(db: AsyncSession = Depends(get_db)) -> VoceProgrammaCatalogoService:
    return VoceProgrammaCatalogoService(
        VoceProgrammaCatalogoRepository(db), LookupRepository(db, TipoCorso)
    )


@router.get(
    "/",
    response_model=PagedResponse[VoceProgrammaCatalogoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_catalogo_programmi(
    tipo_corso_codice: int | None = Query(None),
    attiva: bool | None = Query(None),
    params: PageParams = Depends(),
    service: VoceProgrammaCatalogoService = Depends(get_service),
) -> PagedResponse[VoceProgrammaCatalogoResponse]:
    return await service.get_all(
        params, tipo_corso_codice=tipo_corso_codice, attiva=attiva
    )


@router.get(
    "/{voce_id}",
    response_model=VoceProgrammaCatalogoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_voce_programma_catalogo(
    voce_id: int, service: VoceProgrammaCatalogoService = Depends(get_service)
) -> VoceProgrammaCatalogoResponse:
    try:
        return await service.get_by_id(voce_id)
    except VoceProgrammaCatalogoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=VoceProgrammaCatalogoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_voce_programma_catalogo(
    data: VoceProgrammaCatalogoCreate,
    service: VoceProgrammaCatalogoService = Depends(get_service),
) -> VoceProgrammaCatalogoResponse:
    try:
        return await service.create(data)
    except LookupNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except VoceProgrammaCatalogoDuplicataError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch(
    "/{voce_id}",
    response_model=VoceProgrammaCatalogoResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_voce_programma_catalogo(
    voce_id: int,
    data: VoceProgrammaCatalogoUpdate,
    service: VoceProgrammaCatalogoService = Depends(get_service),
) -> VoceProgrammaCatalogoResponse:
    try:
        return await service.update(voce_id, data)
    except VoceProgrammaCatalogoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except VoceProgrammaCatalogoDuplicataError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
