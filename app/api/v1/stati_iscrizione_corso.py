from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.lookups import StatoIscrizioneCorso
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    StatoIscrizioneCorsoCreate,
    StatoIscrizioneCorsoResponse,
    StatoIscrizioneCorsoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/stati-iscrizione-corso", tags=["stati-iscrizione-corso"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[StatoIscrizioneCorsoResponse]:
    return LookupService(
        LookupRepository(db, StatoIscrizioneCorso),
        StatoIscrizioneCorsoResponse,
        "Stato iscrizione corso",
    )


@router.get(
    "/",
    response_model=PagedResponse[StatoIscrizioneCorsoResponse],
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def list_stati_iscrizione_corso(
    params: PageParams = Depends(),
    service: LookupService[StatoIscrizioneCorsoResponse] = Depends(get_service),
) -> PagedResponse[StatoIscrizioneCorsoResponse]:
    return await service.get_all(params)


@router.get(
    "/{codice}",
    response_model=StatoIscrizioneCorsoResponse,
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def get_stato_iscrizione_corso(
    codice: int,
    service: LookupService[StatoIscrizioneCorsoResponse] = Depends(get_service),
) -> StatoIscrizioneCorsoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/",
    response_model=StatoIscrizioneCorsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def create_stato_iscrizione_corso(
    data: StatoIscrizioneCorsoCreate,
    service: LookupService[StatoIscrizioneCorsoResponse] = Depends(get_service),
) -> StatoIscrizioneCorsoResponse:
    return await service.create(data)


@router.patch(
    "/{codice}",
    response_model=StatoIscrizioneCorsoResponse,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def update_stato_iscrizione_corso(
    codice: int,
    data: StatoIscrizioneCorsoUpdate,
    service: LookupService[StatoIscrizioneCorsoResponse] = Depends(get_service),
) -> StatoIscrizioneCorsoResponse:
    return await service.update(codice, data)


@router.delete(
    "/{codice}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def delete_stato_iscrizione_corso(
    codice: int,
    service: LookupService[StatoIscrizioneCorsoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
