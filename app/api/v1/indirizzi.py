from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.schemas.indirizzo import IndirizzoCreate, IndirizzoResponse, IndirizzoUpdate
from app.services.indirizzo_service import IndirizzoService

router = APIRouter(prefix="/indirizzi", tags=["indirizzi"])


def get_service(db: AsyncSession = Depends(get_db)) -> IndirizzoService:
    return IndirizzoService(IndirizzoRepository(db))


@router.get("/", response_model=PagedResponse[IndirizzoResponse])
async def list_indirizzi(
    params: PageParams = Depends(),
    service: IndirizzoService = Depends(get_service),
) -> PagedResponse[IndirizzoResponse]:
    return await service.get_all(params)


@router.get("/{indirizzo_id}", response_model=IndirizzoResponse)
async def get_indirizzo(
    indirizzo_id: int, service: IndirizzoService = Depends(get_service)
) -> IndirizzoResponse:
    try:
        return await service.get_by_id(indirizzo_id)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=IndirizzoResponse, status_code=status.HTTP_201_CREATED)
async def create_indirizzo(
    data: IndirizzoCreate, service: IndirizzoService = Depends(get_service)
) -> IndirizzoResponse:
    return await service.create(data)


@router.patch("/{indirizzo_id}", response_model=IndirizzoResponse)
async def update_indirizzo(
    indirizzo_id: int,
    data: IndirizzoUpdate,
    service: IndirizzoService = Depends(get_service),
) -> IndirizzoResponse:
    try:
        return await service.update(indirizzo_id, data)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{indirizzo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_indirizzo(
    indirizzo_id: int, service: IndirizzoService = Depends(get_service)
) -> None:
    try:
        await service.delete(indirizzo_id)
    except IndirizzoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
