from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.lookups import Strumento
from app.repositories.lookup import LookupRepository
from app.schemas.lookups import StrumentoCreate, StrumentoResponse, StrumentoUpdate
from app.services.lookup import LookupService

router = APIRouter(prefix="/strumenti", tags=["strumenti"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[StrumentoResponse]:
    return LookupService(
        LookupRepository(db, Strumento), StrumentoResponse, "Strumento"
    )


@router.get("/", response_model=PagedResponse[StrumentoResponse])
async def list_strumenti(
    params: PageParams = Depends(),
    service: LookupService[StrumentoResponse] = Depends(get_service),
) -> PagedResponse[StrumentoResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=StrumentoResponse)
async def get_strumento(
    codice: int, service: LookupService[StrumentoResponse] = Depends(get_service)
) -> StrumentoResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=StrumentoResponse, status_code=status.HTTP_201_CREATED)
async def create_strumento(
    data: StrumentoCreate,
    service: LookupService[StrumentoResponse] = Depends(get_service),
) -> StrumentoResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=StrumentoResponse)
async def update_strumento(
    codice: int,
    data: StrumentoUpdate,
    service: LookupService[StrumentoResponse] = Depends(get_service),
) -> StrumentoResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strumento(
    codice: int, service: LookupService[StrumentoResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)
