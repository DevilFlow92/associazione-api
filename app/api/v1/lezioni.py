from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.corso import CorsoNotFoundError
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.lezione import LezioneNotFoundError
from app.repositories.corso_repository import CorsoRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.lezione_repository import LezioneRepository
from app.schemas.lezione import LezioneCreate, LezioneResponse, LezioneUpdate
from app.services.lezione_service import LezioneService

router = APIRouter(prefix="/lezioni", tags=["lezioni"])


def get_service(db: AsyncSession = Depends(get_db)) -> LezioneService:
    return LezioneService(
        LezioneRepository(db), CorsoRepository(db), IndirizzoRepository(db)
    )


@router.get(
    "/",
    response_model=PagedResponse[LezioneResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_lezioni(
    corso_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: LezioneService = Depends(get_service),
) -> PagedResponse[LezioneResponse]:
    return await service.get_all(params, corso_id=corso_id)


@router.get(
    "/{lezione_id}",
    response_model=LezioneResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_lezione(
    lezione_id: int, service: LezioneService = Depends(get_service)
) -> LezioneResponse:
    try:
        return await service.get_by_id(lezione_id)
    except LezioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=LezioneResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_lezione(
    data: LezioneCreate, service: LezioneService = Depends(get_service)
) -> LezioneResponse:
    try:
        return await service.create(data)
    except (CorsoNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{lezione_id}",
    response_model=LezioneResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_lezione(
    lezione_id: int,
    data: LezioneUpdate,
    service: LezioneService = Depends(get_service),
) -> LezioneResponse:
    try:
        return await service.update(lezione_id, data)
    except (LezioneNotFoundError, CorsoNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{lezione_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def delete_lezione(
    lezione_id: int, service: LezioneService = Depends(get_service)
) -> None:
    try:
        await service.delete(lezione_id)
    except LezioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
