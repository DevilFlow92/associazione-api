"""Router della scheda alunno.

Due superfici distinte, deliberatamente NON fuse in un unico GET:

- ``/schede-alunno/...`` — CRUD del personale corsi, protetto dal solo RBAC
  resource:action (``corsi:read`` in lettura, ``corsi:write`` in scrittura),
  esattamente come gli altri router del progetto;
- ``/schede-alunno/me/{iscrizione_corso_id}`` — accesso dell'alunno alla
  propria scheda, protetto dal controllo row-level.

Un unico ``GET /schede-alunno/{id}`` che ospiti entrambe le logiche dovrebbe
concedere l'accesso a chiunque sia autenticato per poi negarlo dall'interno:
la guardia dichiarativa del router non potrebbe più esprimere il requisito, e
ogni futura modifica al corpo rischierebbe di aprire la lettura a tutti. Con
due percorsi separati ciascun endpoint ha una regola sola e leggibile, e
l'endpoint dell'alunno è indicizzato per ``iscrizione_corso_id`` — l'alunno
conosce la propria iscrizione, non l'id della scheda che non ha mai visto.
"""

from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import (
    AccessoSchedaAlunnoNegatoError,
    SchedaAlunnoDuplicataError,
    SchedaAlunnoIscrizioneNotFoundError,
    SchedaAlunnoNotFoundError,
)
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.schemas.scheda_alunno import (
    SchedaAlunnoCreate,
    SchedaAlunnoResponse,
    SchedaAlunnoUpdate,
)
from app.services.scheda_alunno_service import SchedaAlunnoService

router = APIRouter(prefix="/schede-alunno", tags=["schede-alunno"])


def get_service(db: AsyncSession = Depends(get_db)) -> SchedaAlunnoService:
    return SchedaAlunnoService(
        SchedaAlunnoRepository(db), IscrizioneCorsoRepository(db)
    )


def _forbidden(e: AccessoSchedaAlunnoNegatoError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


def _not_found(e: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Accesso dell'alunno alla propria scheda (row-level) ──────────────────────


@router.get("/me/{iscrizione_corso_id}", response_model=SchedaAlunnoResponse)
async def get_propria_scheda_alunno(
    iscrizione_corso_id: int,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    """Scheda dell'iscrizione indicata, se il chiamante ne ha titolo.

    Nessun permesso ``corsi:*`` richiesto — è il punto: l'alunno non ne ha.
    L'autorizzazione è interamente row-level (vedi ``rbac_row_level``).
    """
    try:
        return await service.get_propria_scheda(iscrizione_corso_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (IscrizioneCorsoNotFoundError, SchedaAlunnoIscrizioneNotFoundError) as e:
        raise _not_found(e) from e


# ── CRUD del personale corsi ─────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PagedResponse[SchedaAlunnoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_schede_alunno(
    iscrizione_corso_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: SchedaAlunnoService = Depends(get_service),
) -> PagedResponse[SchedaAlunnoResponse]:
    return await service.get_all(params, iscrizione_corso_id=iscrizione_corso_id)


@router.get(
    "/{scheda_alunno_id}",
    response_model=SchedaAlunnoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_scheda_alunno(
    scheda_alunno_id: int, service: SchedaAlunnoService = Depends(get_service)
) -> SchedaAlunnoResponse:
    try:
        return await service.get_by_id(scheda_alunno_id)
    except SchedaAlunnoNotFoundError as e:
        raise _not_found(e) from e


@router.post(
    "/", response_model=SchedaAlunnoResponse, status_code=status.HTTP_201_CREATED
)
async def create_scheda_alunno(
    data: SchedaAlunnoCreate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    try:
        return await service.create(data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except IscrizioneCorsoNotFoundError as e:
        raise _not_found(e) from e
    except SchedaAlunnoDuplicataError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{scheda_alunno_id}", response_model=SchedaAlunnoResponse)
async def update_scheda_alunno(
    scheda_alunno_id: int,
    data: SchedaAlunnoUpdate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    try:
        return await service.update(scheda_alunno_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e


@router.delete("/{scheda_alunno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheda_alunno(
    scheda_alunno_id: int,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> None:
    try:
        await service.delete(scheda_alunno_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e
