"""Portale alunno: viste self-service, sola lettura, sulla propria iscrizione.

Superficie separata da ``/iscrizioni-corso``, ``/lezioni``, ``/presenze`` e
``/pagamenti-corso`` (che restano riservati al personale con ``corsi:*``,
stesso motivo per cui ``/schede-alunno/me/...`` è un endpoint a parte
rispetto a ``/schede-alunno/...``): qui nessun permesso ``corsi:*`` è mai
richiesto o concesso, l'unica autorizzazione è essere la Persona titolare
dell'iscrizione (``rbac_row_level.assert_e_titolare_iscrizione``).

Tutto sotto ``/me`` perché non è un'estensione di un'unica risorsa CRUD ma
un punto di ingresso trasversale: l'alunno scopre le proprie iscrizioni
(``GET /me/iscrizioni-corso``) e da lì naviga calendario, presenze e
pagamenti di ciascuna.
"""

from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.portale_alunno import AccessoPortaleAlunnoNegatoError
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lezione_repository import LezioneRepository
from app.repositories.pagamento_corso_repository import PagamentoCorsoRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.schemas.iscrizione_corso import IscrizioneCorsoResponse
from app.schemas.lezione import LezioneResponse
from app.schemas.pagamento_corso import PagamentoCorsoResponse
from app.schemas.presenza import PresenzaResponse
from app.services.portale_alunno_service import PortaleAlunnoService

router = APIRouter(prefix="/me", tags=["portale-alunno"])


def get_service(db: AsyncSession = Depends(get_db)) -> PortaleAlunnoService:
    return PortaleAlunnoService(
        IscrizioneCorsoRepository(db),
        LezioneRepository(db),
        PresenzaRepository(db),
        PagamentoCorsoRepository(db),
    )


def _forbidden(e: AccessoPortaleAlunnoNegatoError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


def _not_found(e: IscrizioneCorsoNotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/iscrizioni-corso", response_model=PagedResponse[IscrizioneCorsoResponse])
async def get_mie_iscrizioni_corso(
    params: PageParams = Depends(),
    utente: Utente = Depends(get_current_user),
    service: PortaleAlunnoService = Depends(get_service),
) -> PagedResponse[IscrizioneCorsoResponse]:
    try:
        return await service.get_mie_iscrizioni(params, utente)
    except AccessoPortaleAlunnoNegatoError as e:
        raise _forbidden(e) from e


@router.get(
    "/iscrizioni-corso/{iscrizione_corso_id}/lezioni",
    response_model=PagedResponse[LezioneResponse],
)
async def get_mio_calendario_lezioni(
    iscrizione_corso_id: int,
    params: PageParams = Depends(),
    utente: Utente = Depends(get_current_user),
    service: PortaleAlunnoService = Depends(get_service),
) -> PagedResponse[LezioneResponse]:
    try:
        return await service.get_mio_calendario(iscrizione_corso_id, params, utente)
    except AccessoPortaleAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except IscrizioneCorsoNotFoundError as e:
        raise _not_found(e) from e


@router.get(
    "/iscrizioni-corso/{iscrizione_corso_id}/presenze",
    response_model=PagedResponse[PresenzaResponse],
)
async def get_mie_presenze(
    iscrizione_corso_id: int,
    params: PageParams = Depends(),
    utente: Utente = Depends(get_current_user),
    service: PortaleAlunnoService = Depends(get_service),
) -> PagedResponse[PresenzaResponse]:
    try:
        return await service.get_mie_presenze(iscrizione_corso_id, params, utente)
    except AccessoPortaleAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except IscrizioneCorsoNotFoundError as e:
        raise _not_found(e) from e


@router.get(
    "/iscrizioni-corso/{iscrizione_corso_id}/pagamenti",
    response_model=PagedResponse[PagamentoCorsoResponse],
)
async def get_miei_pagamenti(
    iscrizione_corso_id: int,
    params: PageParams = Depends(),
    utente: Utente = Depends(get_current_user),
    service: PortaleAlunnoService = Depends(get_service),
) -> PagedResponse[PagamentoCorsoResponse]:
    try:
        return await service.get_miei_pagamenti(iscrizione_corso_id, params, utente)
    except AccessoPortaleAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except IscrizioneCorsoNotFoundError as e:
        raise _not_found(e) from e
