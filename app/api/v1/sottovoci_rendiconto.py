from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import SottovoceRendiconto
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import (
    SottovoceRendicontoCreate,
    SottovoceRendicontoResponse,
    SottovoceRendicontoUpdate,
)
from app.services.lookup import LookupService

router = APIRouter(prefix="/sottovoci-rendiconto", tags=["sottovoci-rendiconto"])


def get_service(
    db: AsyncSession = Depends(get_db),
) -> LookupService[SottovoceRendicontoResponse]:
    return LookupService(
        LookupRepository(db, SottovoceRendiconto),
        SottovoceRendicontoResponse,
        "Sottovoce rendiconto",
    )


@router.get("/", response_model=PagedResponse[SottovoceRendicontoResponse])
async def list_sottovoci_rendiconto(
    params: PageParams = Depends(),
    service: LookupService[SottovoceRendicontoResponse] = Depends(get_service),
) -> PagedResponse[SottovoceRendicontoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=SottovoceRendicontoResponse)
async def get_sottovoce_rendiconto(
    codice: int,
    service: LookupService[SottovoceRendicontoResponse] = Depends(get_service),
) -> SottovoceRendicontoResponse:
    return await service.get_by_codice(codice)


@router.post(
    "/",
    response_model=SottovoceRendicontoResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_sottovoce_rendiconto(
    data: SottovoceRendicontoCreate,
    service: LookupService[SottovoceRendicontoResponse] = Depends(get_service),
) -> SottovoceRendicontoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=SottovoceRendicontoResponse)
async def update_sottovoce_rendiconto(
    codice: int,
    data: SottovoceRendicontoUpdate,
    service: LookupService[SottovoceRendicontoResponse] = Depends(get_service),
) -> SottovoceRendicontoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sottovoce_rendiconto(
    codice: int,
    service: LookupService[SottovoceRendicontoResponse] = Depends(get_service),
) -> None:
    await service.delete(codice)
