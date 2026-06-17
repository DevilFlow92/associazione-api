from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.auth import InvalidCredentialsError
from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.utente import (
    RuoloNotFoundError,
    UtenteDuplicateEmailError,
    UtenteNotFoundError,
)
from app.repositories.persona_repository import PersonaRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.repositories.utente_repository import UtenteRepository
from app.schemas.utente import (
    PasswordUpdate,
    UtenteCreate,
    UtenteResponse,
    UtenteUpdate,
)
from app.services.utente_service import UtenteService

router = APIRouter(prefix="/utenti", tags=["utenti"])


def get_service(db: AsyncSession = Depends(get_db)) -> UtenteService:
    return UtenteService(
        UtenteRepository(db), RuoloRepository(db), PersonaRepository(db)
    )


@router.get(
    "/",
    response_model=PagedResponse[UtenteResponse],
    dependencies=[Depends(require_permission("utenti:read"))],
)
async def list_utenti(
    params: PageParams = Depends(),
    service: UtenteService = Depends(get_service),
) -> PagedResponse[UtenteResponse]:
    return await service.get_all(params)


@router.get(
    "/{utente_id}",
    response_model=UtenteResponse,
    dependencies=[Depends(require_permission("utenti:read"))],
)
async def get_utente(
    utente_id: int, service: UtenteService = Depends(get_service)
) -> UtenteResponse:
    try:
        return await service.get_by_id(utente_id)
    except UtenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=UtenteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("utenti:write"))],
)
async def create_utente(
    data: UtenteCreate, service: UtenteService = Depends(get_service)
) -> UtenteResponse:
    try:
        return await service.create(data)
    except InvalidCredentialsError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except RuoloNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except UtenteDuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch(
    "/{utente_id}",
    response_model=UtenteResponse,
    dependencies=[Depends(require_permission("utenti:write"))],
)
async def update_utente(
    utente_id: int, data: UtenteUpdate, service: UtenteService = Depends(get_service)
) -> UtenteResponse:
    try:
        return await service.update(utente_id, data)
    except UtenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (PersonaNotFoundError, RuoloNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put(
    "/{utente_id}/password",
    response_model=UtenteResponse,
    dependencies=[Depends(require_permission("utenti:write"))],
)
async def set_password(
    utente_id: int,
    data: PasswordUpdate,
    service: UtenteService = Depends(get_service),
) -> UtenteResponse:
    try:
        return await service.set_password(utente_id, data.password)
    except UtenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{utente_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("utenti:write"))],
)
async def delete_utente(
    utente_id: int, service: UtenteService = Depends(get_service)
) -> None:
    try:
        await service.delete(utente_id)
    except UtenteNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
