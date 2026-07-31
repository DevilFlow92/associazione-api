from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.allievo import (
    AllievoDuplicateCodiceError,
    AllievoNotFoundError,
    AllievoPersonaAlreadyLinkedError,
)
from app.exceptions.persona import PersonaNotFoundError
from app.repositories.allievo_repository import AllievoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.allievo import AllievoCreate, AllievoResponse, AllievoUpdate
from app.services.allievo_service import AllievoService

router = APIRouter(prefix="/allievi", tags=["allievi"])


def get_service(db: AsyncSession = Depends(get_db)) -> AllievoService:
    return AllievoService(AllievoRepository(db), PersonaRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[AllievoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_allievi(
    banda_codice: int | None = Query(None),
    params: PageParams = Depends(),
    service: AllievoService = Depends(get_service),
) -> PagedResponse[AllievoResponse]:
    return await service.get_all(params, banda_codice=banda_codice)


@router.get(
    "/{allievo_id}",
    response_model=AllievoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_allievo(
    allievo_id: int, service: AllievoService = Depends(get_service)
) -> AllievoResponse:
    try:
        return await service.get_by_id(allievo_id)
    except AllievoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=AllievoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_allievo(
    data: AllievoCreate, service: AllievoService = Depends(get_service)
) -> AllievoResponse:
    try:
        return await service.create(data)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (AllievoDuplicateCodiceError, AllievoPersonaAlreadyLinkedError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch(
    "/{allievo_id}",
    response_model=AllievoResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_allievo(
    allievo_id: int,
    data: AllievoUpdate,
    service: AllievoService = Depends(get_service),
) -> AllievoResponse:
    try:
        return await service.update(allievo_id, data)
    except AllievoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AllievoDuplicateCodiceError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{allievo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def delete_allievo(
    allievo_id: int, service: AllievoService = Depends(get_service)
) -> None:
    try:
        await service.delete(allievo_id)
    except AllievoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
