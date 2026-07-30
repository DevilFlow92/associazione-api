from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.committente import (
    CommittenteHasServiziError,
    CommittenteNotFoundError,
)
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.repositories.committente_repository import CommittenteRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.schemas.committente import (
    CommittenteCreate,
    CommittenteResponse,
    CommittenteUpdate,
)
from app.services.committente_service import CommittenteService

router = APIRouter(prefix="/committenti", tags=["committenti"])


def get_service(db: AsyncSession = Depends(get_db)) -> CommittenteService:
    return CommittenteService(CommittenteRepository(db), IndirizzoRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[CommittenteResponse],
    dependencies=[Depends(require_permission("servizi:read"))],
)
async def list_committenti(
    params: PageParams = Depends(),
    service: CommittenteService = Depends(get_service),
) -> PagedResponse[CommittenteResponse]:
    return await service.get_all(params)


@router.get(
    "/{committente_id}",
    response_model=CommittenteResponse,
    dependencies=[Depends(require_permission("servizi:read"))],
)
async def get_committente(
    committente_id: int, service: CommittenteService = Depends(get_service)
) -> CommittenteResponse:
    try:
        return await service.get_by_id(committente_id)
    except CommittenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=CommittenteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("servizi:write"))],
)
async def create_committente(
    data: CommittenteCreate, service: CommittenteService = Depends(get_service)
) -> CommittenteResponse:
    try:
        return await service.create(data)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{committente_id}",
    response_model=CommittenteResponse,
    dependencies=[Depends(require_permission("servizi:write"))],
)
async def update_committente(
    committente_id: int,
    data: CommittenteUpdate,
    service: CommittenteService = Depends(get_service),
) -> CommittenteResponse:
    try:
        return await service.update(committente_id, data)
    except (CommittenteNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{committente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("servizi:write"))],
)
async def delete_committente(
    committente_id: int, service: CommittenteService = Depends(get_service)
) -> None:
    try:
        await service.delete(committente_id)
    except CommittenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CommittenteHasServiziError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
