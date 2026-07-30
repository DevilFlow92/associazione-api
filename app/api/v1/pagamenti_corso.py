from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.pagamento_corso import PagamentoCorsoNotFoundError
from app.models.lookups import NaturaFlusso
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.lookup import LookupRepository
from app.repositories.pagamento_corso_repository import PagamentoCorsoRepository
from app.repositories.ricevuta_repository import RicevutaRepository
from app.schemas.pagamento_corso import (
    PagamentoCorsoCreate,
    PagamentoCorsoResponse,
    PagamentoCorsoUpdate,
)
from app.services.pagamento_corso_service import PagamentoCorsoService

router = APIRouter(prefix="/pagamenti-corso", tags=["pagamenti-corso"])


def get_service(db: AsyncSession = Depends(get_db)) -> PagamentoCorsoService:
    return PagamentoCorsoService(
        PagamentoCorsoRepository(db),
        IscrizioneCorsoRepository(db),
        RicevutaRepository(db),
        FlussoCassaRepository(db),
        ConfigurazioneBandaAnnoRepository(db),
        LookupRepository(db, NaturaFlusso),
    )


@router.get(
    "/",
    response_model=PagedResponse[PagamentoCorsoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_pagamenti_corso(
    iscrizione_corso_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: PagamentoCorsoService = Depends(get_service),
) -> PagedResponse[PagamentoCorsoResponse]:
    return await service.get_all(iscrizione_corso_id, params)


@router.get(
    "/{pagamento_corso_id}",
    response_model=PagamentoCorsoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_pagamento_corso(
    pagamento_corso_id: int, service: PagamentoCorsoService = Depends(get_service)
) -> PagamentoCorsoResponse:
    try:
        return await service.get_by_id(pagamento_corso_id)
    except PagamentoCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=PagamentoCorsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def create_pagamento_corso(
    data: PagamentoCorsoCreate, service: PagamentoCorsoService = Depends(get_service)
) -> PagamentoCorsoResponse:
    try:
        return await service.create(data)
    except IscrizioneCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{pagamento_corso_id}",
    response_model=PagamentoCorsoResponse,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def update_pagamento_corso(
    pagamento_corso_id: int,
    data: PagamentoCorsoUpdate,
    service: PagamentoCorsoService = Depends(get_service),
) -> PagamentoCorsoResponse:
    try:
        return await service.update(pagamento_corso_id, data)
    except PagamentoCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{pagamento_corso_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("corsi:write"))],
)
async def delete_pagamento_corso(
    pagamento_corso_id: int, service: PagamentoCorsoService = Depends(get_service)
) -> None:
    try:
        await service.delete(pagamento_corso_id)
    except PagamentoCorsoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
