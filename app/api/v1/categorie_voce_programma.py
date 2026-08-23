from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.models.lookups import CategoriaVoceProgramma
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    CategoriaVoceProgrammaCreate,
    CategoriaVoceProgrammaResponse,
    CategoriaVoceProgrammaUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(
    prefix="/categorie-voce-programma", tags=["categorie-voce-programma"]
)


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[CategoriaVoceProgrammaResponse]:
    return LookupService(
        LookupRepository(db, CategoriaVoceProgramma),
        CategoriaVoceProgrammaResponse,
        "Categoria voce programma",
    )


@router.get(
    "/",
    response_model=PagedResponse[CategoriaVoceProgrammaResponse],
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def list_categorie_voce_programma(
    params: PageParams = Depends(),
    service: LookupService[CategoriaVoceProgrammaResponse] = Depends(get_service),
) -> PagedResponse[CategoriaVoceProgrammaResponse]:
    return await service.get_all(params)


@router.get(
    "/{codice}",
    response_model=CategoriaVoceProgrammaResponse,
    dependencies=[Depends(require_permission("lookup:read"))],
)
async def get_categoria_voce_programma(
    codice: int,
    service: LookupService[CategoriaVoceProgrammaResponse] = Depends(get_service),
) -> CategoriaVoceProgrammaResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/",
    response_model=CategoriaVoceProgrammaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def create_categoria_voce_programma(
    data: CategoriaVoceProgrammaCreate,
    service: LookupService[CategoriaVoceProgrammaResponse] = Depends(get_service),
) -> CategoriaVoceProgrammaResponse:
    return await service.create(data)


@router.patch(
    "/{codice}",
    response_model=CategoriaVoceProgrammaResponse,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def update_categoria_voce_programma(
    codice: int,
    data: CategoriaVoceProgrammaUpdate,
    service: LookupService[CategoriaVoceProgrammaResponse] = Depends(get_service),
) -> CategoriaVoceProgrammaResponse:
    return await service.update(codice, data)


@router.delete(
    "/{codice}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("lookup:write"))],
)
async def delete_categoria_voce_programma(
    codice: int,
    service: LookupService[CategoriaVoceProgrammaResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
