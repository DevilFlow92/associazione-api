from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.repositories.permesso_repository import PermessoRepository
from app.schemas.permesso import PermessoResponse
from app.services.permesso_service import PermessoService

router = APIRouter(prefix="/permessi", tags=["permessi"])


def get_service(db: AsyncSession = Depends(get_db)) -> PermessoService:
    return PermessoService(PermessoRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[PermessoResponse],
    dependencies=[Depends(require_permission("ruoli:read"))],
)
async def list_permessi(
    params: PageParams = Depends(),
    service: PermessoService = Depends(get_service),
) -> PagedResponse[PermessoResponse]:
    """Catalogo dei permessi disponibili (sola lettura: sono dati di codice)."""
    return await service.get_all(params)
