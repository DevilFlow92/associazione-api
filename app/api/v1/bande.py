from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.models.lookups import Banda
from app.repositories.banda_indirizzo_repository import BandaIndirizzoRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.lookup import LookupRepository
from app.schemas.indirizzo import IndirizzoResponse
from app.schemas.lookups import BandaCreate, BandaResponse, BandaUpdate
from app.services.banda_indirizzo_service import BandaIndirizzoService
from app.services.lookup import LookupService

router = APIRouter(prefix="/bande", tags=["bande"])


def get_service(db: AsyncSession = Depends(get_db)) -> LookupService[BandaResponse]:
    return LookupService(LookupRepository(db, Banda), BandaResponse, "Banda")


def get_indirizzo_service(
    db: AsyncSession = Depends(get_db),
) -> BandaIndirizzoService:
    return BandaIndirizzoService(BandaIndirizzoRepository(db), IndirizzoRepository(db))


@router.get("/", response_model=PagedResponse[BandaResponse])
async def list_bande(
    params: PageParams = Depends(),
    service: LookupService[BandaResponse] = Depends(get_service),
) -> PagedResponse[BandaResponse]:
    return await service.get_all(params)


@router.get("/{codice}", response_model=BandaResponse)
async def get_banda(
    codice: int, service: LookupService[BandaResponse] = Depends(get_service)
) -> BandaResponse:
    return await service.get_by_codice(codice)


@router.post("/", response_model=BandaResponse, status_code=status.HTTP_201_CREATED)
async def create_banda(
    data: BandaCreate, service: LookupService[BandaResponse] = Depends(get_service)
) -> BandaResponse:
    return await service.create(data)


@router.patch("/{codice}", response_model=BandaResponse)
async def update_banda(
    codice: int,
    data: BandaUpdate,
    service: LookupService[BandaResponse] = Depends(get_service),
) -> BandaResponse:
    return await service.update(codice, data)


@router.delete("/{codice}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_banda(
    codice: int, service: LookupService[BandaResponse] = Depends(get_service)
) -> None:
    await service.delete(codice)


# ── Indirizzi della banda (relazione molti-a-molti) ──────────────────────────
@router.get("/{codice}/indirizzi", response_model=list[IndirizzoResponse])
async def list_indirizzi_banda(
    codice: int,
    service: BandaIndirizzoService = Depends(get_indirizzo_service),
) -> list[IndirizzoResponse]:
    return await service.get_indirizzi(codice)


@router.put(
    "/{codice}/indirizzi/{indirizzo_id}", response_model=list[IndirizzoResponse]
)
async def add_indirizzo_banda(
    codice: int,
    indirizzo_id: int,
    service: BandaIndirizzoService = Depends(get_indirizzo_service),
) -> list[IndirizzoResponse]:
    try:
        return await service.add_indirizzo(codice, indirizzo_id)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{codice}/indirizzi/{indirizzo_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def remove_indirizzo_banda(
    codice: int,
    indirizzo_id: int,
    service: BandaIndirizzoService = Depends(get_indirizzo_service),
) -> None:
    try:
        await service.remove_indirizzo(codice, indirizzo_id)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
