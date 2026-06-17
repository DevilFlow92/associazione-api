from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.utente import (
    PermessoNotFoundError,
    RuoloDuplicateNomeError,
    RuoloNotFoundError,
)
from app.repositories.permesso_repository import PermessoRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.schemas.ruolo import RuoloCreate, RuoloResponse, RuoloUpdate
from app.services.ruolo_service import RuoloService

router = APIRouter(prefix="/ruoli", tags=["ruoli"])


def get_service(db: AsyncSession = Depends(get_db)) -> RuoloService:
    return RuoloService(RuoloRepository(db), PermessoRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[RuoloResponse],
    dependencies=[Depends(require_permission("ruoli:read"))],
)
async def list_ruoli(
    params: PageParams = Depends(),
    service: RuoloService = Depends(get_service),
) -> PagedResponse[RuoloResponse]:
    return await service.get_all(params)


@router.get(
    "/{ruolo_id}",
    response_model=RuoloResponse,
    dependencies=[Depends(require_permission("ruoli:read"))],
)
async def get_ruolo(
    ruolo_id: int, service: RuoloService = Depends(get_service)
) -> RuoloResponse:
    try:
        return await service.get_by_id(ruolo_id)
    except RuoloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=RuoloResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("ruoli:write"))],
)
async def create_ruolo(
    data: RuoloCreate, service: RuoloService = Depends(get_service)
) -> RuoloResponse:
    try:
        return await service.create(data)
    except PermessoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuoloDuplicateNomeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch(
    "/{ruolo_id}",
    response_model=RuoloResponse,
    dependencies=[Depends(require_permission("ruoli:write"))],
)
async def update_ruolo(
    ruolo_id: int, data: RuoloUpdate, service: RuoloService = Depends(get_service)
) -> RuoloResponse:
    try:
        return await service.update(ruolo_id, data)
    except RuoloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermessoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuoloDuplicateNomeError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{ruolo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("ruoli:write"))],
)
async def delete_ruolo(
    ruolo_id: int, service: RuoloService = Depends(get_service)
) -> None:
    try:
        await service.delete(ruolo_id)
    except RuoloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
