from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.socio import SocioDuplicateEmailError, SocioNotFoundError
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioResponse, SocioUpdate
from app.services.socio_service import SocioService

router = APIRouter(prefix="/soci", tags=["soci"])


def get_service(db: AsyncSession = Depends(get_db)) -> SocioService:
    return SocioService(SocioRepository(db))


@router.get("/", response_model=PagedResponse[SocioResponse])
async def list_soci(
    params: PageParams = Depends(),
    service: SocioService = Depends(get_service),
) -> PagedResponse[SocioResponse]:
    return await service.get_all(params)


@router.get("/{socio_id}", response_model=SocioResponse)
async def get_socio(
    socio_id: int, service: SocioService = Depends(get_service)
) -> SocioResponse:
    try:
        return await service.get_by_id(socio_id)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=SocioResponse, status_code=status.HTTP_201_CREATED)
async def create_socio(
    data: SocioCreate, service: SocioService = Depends(get_service)
) -> SocioResponse:
    try:
        return await service.create(data)
    except SocioDuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{socio_id}", response_model=SocioResponse)
async def update_socio(
    socio_id: int, data: SocioUpdate, service: SocioService = Depends(get_service)
) -> SocioResponse:
    try:
        return await service.update(socio_id, data)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except SocioDuplicateEmailError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_socio(
    socio_id: int, service: SocioService = Depends(get_service)
) -> None:
    try:
        await service.delete(socio_id)
    except SocioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
