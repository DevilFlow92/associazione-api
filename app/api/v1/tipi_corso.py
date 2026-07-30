from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.lookups import TipoCorso
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import TipoCorsoCreate, TipoCorsoResponse, TipoCorsoUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/tipi-corso", tags=["tipi-corso"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[TipoCorsoResponse]:
    return LookupService(
        LookupRepository(db, TipoCorso), TipoCorsoResponse, "Tipo corso"
    )


@router.get(
    "/",
    response_model=PagedResponse[TipoCorsoResponse],
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def list_tipi_corso(
    params: PageParams = Depends(),
    service: LookupService[TipoCorsoResponse] = Depends(get_service),
) -> PagedResponse[TipoCorsoResponse]:
    return await service.get_all(params)


@router.get(
    "/{codice}",
    response_model=TipoCorsoResponse,
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def get_tipo_corso(
    codice: int, service: LookupService[TipoCorsoResponse] = Depends(get_service)
) -> TipoCorsoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/",
    response_model=TipoCorsoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def create_tipo_corso(
    data: TipoCorsoCreate,
    service: LookupService[TipoCorsoResponse] = Depends(get_service),
) -> TipoCorsoResponse:
    return await service.create(data)


@router.patch(
    "/{codice}",
    response_model=TipoCorsoResponse,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def update_tipo_corso(
    codice: int,
    data: TipoCorsoUpdate,
    service: LookupService[TipoCorsoResponse] = Depends(get_service),
) -> TipoCorsoResponse:
    return await service.update(codice, data)


@router.delete(
    "/{codice}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def delete_tipo_corso(
    codice: int, service: LookupService[TipoCorsoResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
