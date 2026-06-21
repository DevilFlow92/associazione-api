from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.lookups import SezioneRendiconto, SottovoceRendiconto, VoceRendiconto
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.lookup import LookupRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.rendiconto import RendicontoResponse
from app.services.rendiconto_service import RendicontoService
from app.utils.export_rendiconto import (
    render_rendiconto_pdf,
    render_rendiconto_xlsx,
)

PDF_MEDIA_TYPE = "application/pdf"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

router = APIRouter(prefix="/contabilita", tags=["contabilita"])


def get_service(db: AsyncSession = Depends(get_db)) -> RendicontoService:
    return RendicontoService(
        flusso_repo=FlussoCassaRepository(db),
        cfg_repo=ConfigurazioneBandaAnnoRepository(db),
        voce_contabilita_repo=VoceContabilitaRepository(db),
        sezione_repo=LookupRepository(db, SezioneRendiconto),
        voce_rendiconto_repo=LookupRepository(db, VoceRendiconto),
        sottovoce_repo=LookupRepository(db, SottovoceRendiconto),
    )


@router.get(
    "/rendiconto/",
    response_model=RendicontoResponse,
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def get_rendiconto(
    banda_codice: int = Query(...),
    anno: int = Query(...),
    service: RendicontoService = Depends(get_service),
) -> RendicontoResponse:
    return await service.get_rendiconto(banda_codice, anno)


@router.get(
    "/rendiconto/export/pdf",
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def export_rendiconto_pdf(
    banda_codice: int = Query(...),
    anno: int = Query(...),
    service: RendicontoService = Depends(get_service),
) -> Response:
    data = await service.get_rendiconto(banda_codice, anno)
    content = render_rendiconto_pdf(data)
    filename = f"rendiconto_{banda_codice}_{anno}.pdf"
    return Response(
        content=content,
        media_type=PDF_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/rendiconto/export/xlsx",
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def export_rendiconto_xlsx(
    banda_codice: int = Query(...),
    anno: int = Query(...),
    service: RendicontoService = Depends(get_service),
) -> Response:
    data = await service.get_rendiconto(banda_codice, anno)
    content = render_rendiconto_xlsx(data)
    filename = f"rendiconto_{banda_codice}_{anno}.xlsx"
    return Response(
        content=content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
