from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.exceptions.lezione import LezioneNotFoundError
from app.exceptions.persona import PersonaNotFoundError
from app.exceptions.presenza import (
    PresenzaContainerMismatchError,
    PresenzaNotFoundError,
)
from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.models.utente import Utente
from app.repositories.lezione_repository import LezioneRepository
from app.repositories.persona_repository import PersonaRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.presenza import (
    PresenzaBulkUpdate,
    PresenzaBulkUpdateResponse,
    PresenzaCreate,
    PresenzaResponse,
    PresenzaUpdate,
)
from app.services.presenza_service import PresenzaService

router = APIRouter(prefix="/presenze", tags=["presenze"])


def get_service(db: AsyncSession = Depends(get_db)) -> PresenzaService:
    return PresenzaService(
        PresenzaRepository(db),
        PersonaRepository(db),
        ServizioRepository(db),
        ProvaRepository(db),
        LezioneRepository(db),
    )


def _permesso_per_container(
    *,
    servizio_id: int | None,
    prova_id: int | None,
    lezione_id: int | None,
    azione: str,
) -> str:
    """Corsi e Servizi/Prove sono domini di permesso volutamente separati
    (``corsi:read/write`` introdotto nella card #171): una Presenza
    orientata a una Lezione richiede il permesso ``corsi:*`` del suo Corso,
    non ``servizi:*``."""
    if lezione_id is not None:
        return f"corsi:{azione}"
    return f"servizi:{azione}"


def _check_permesso(user: Utente, codice: str) -> None:
    if not (user.superuser or codice in user.permessi):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permesso richiesto: {codice}",
        )


@router.get(
    "/servizio/{servizio_id}",
    response_model=PagedResponse[PresenzaResponse],
    dependencies=[Depends(require_permission("servizi:read"))],
)
async def get_organico_servizio(
    servizio_id: int,
    params: PageParams = Depends(),
    service: PresenzaService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_by_servizio(servizio_id, params)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/prova/{prova_id}",
    response_model=PagedResponse[PresenzaResponse],
    dependencies=[Depends(require_permission("servizi:read"))],
)
async def get_organico_prova(
    prova_id: int,
    params: PageParams = Depends(),
    service: PresenzaService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_by_prova(prova_id, params)
    except ProvaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/lezione/{lezione_id}",
    response_model=PagedResponse[PresenzaResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_organico_lezione(
    lezione_id: int,
    params: PageParams = Depends(),
    service: PresenzaService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_by_lezione(lezione_id, params)
    except LezioneNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{presenza_id}",
    response_model=PresenzaResponse,
    dependencies=[Depends(require_permission("servizi:read"))],
)
async def get_presenza(
    presenza_id: int, service: PresenzaService = Depends(get_service)
) -> PresenzaResponse:
    try:
        return await service.get_by_id(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=PresenzaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_presenza(
    data: PresenzaCreate,
    user: Utente = Depends(get_current_user),
    service: PresenzaService = Depends(get_service),
) -> PresenzaResponse:
    _check_permesso(
        user,
        _permesso_per_container(
            servizio_id=data.servizio_id,
            prova_id=data.prova_id,
            lezione_id=data.lezione_id,
            azione="write",
        ),
    )
    try:
        return await service.create(data)
    except (
        PersonaNotFoundError,
        ServizioNotFoundError,
        ProvaNotFoundError,
        LezioneNotFoundError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/bulk",
    response_model=PresenzaBulkUpdateResponse,
    dependencies=[Depends(require_permission("servizi:write"))],
)
async def bulk_update_presenze(
    data: PresenzaBulkUpdate,
    service: PresenzaService = Depends(get_service),
) -> PresenzaBulkUpdateResponse:
    try:
        items = await service.bulk_update(data)
        return PresenzaBulkUpdateResponse(items=items)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PresenzaContainerMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.patch(
    "/{presenza_id}",
    response_model=PresenzaResponse,
)
async def update_presenza(
    presenza_id: int,
    data: PresenzaUpdate,
    user: Utente = Depends(get_current_user),
    service: PresenzaService = Depends(get_service),
) -> PresenzaResponse:
    # Il permesso dipende dal contenitore (servizio/prova vs lezione), noto
    # solo dopo aver caricato la Presenza esistente: niente dependencies=
    # statiche, il controllo va fatto qui dopo il fetch.
    try:
        esistente = await service.get_by_id(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    _check_permesso(
        user,
        _permesso_per_container(
            servizio_id=esistente.servizio_id,
            prova_id=esistente.prova_id,
            lezione_id=esistente.lezione_id,
            azione="write",
        ),
    )
    try:
        return await service.update(presenza_id, data)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{presenza_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_presenza(
    presenza_id: int,
    user: Utente = Depends(get_current_user),
    service: PresenzaService = Depends(get_service),
) -> None:
    try:
        esistente = await service.get_by_id(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    _check_permesso(
        user,
        _permesso_per_container(
            servizio_id=esistente.servizio_id,
            prova_id=esistente.prova_id,
            lezione_id=esistente.lezione_id,
            azione="write",
        ),
    )
    try:
        await service.delete(presenza_id)
    except PresenzaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
