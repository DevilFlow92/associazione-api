from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.check_quote import CheckQuoteResponse
from app.services.check_quote_service import CheckQuoteService

router = APIRouter(prefix="/contabilita", tags=["contabilita"])


def get_service(db: AsyncSession = Depends(get_db)) -> CheckQuoteService:
    return CheckQuoteService(
        cfg_repo=ConfigurazioneBandaAnnoRepository(db),
        socio_repo=SocioRepository(db),
        iscrizione_repo=IscrizioneRepository(db),
    )


@router.get(
    "/check-quote/",
    response_model=CheckQuoteResponse,
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def get_check_quote(
    banda_codice: int = Query(...),
    anno: int = Query(...),
    service: CheckQuoteService = Depends(get_service),
) -> CheckQuoteResponse:
    return await service.get_check_quote(banda_codice, anno)
