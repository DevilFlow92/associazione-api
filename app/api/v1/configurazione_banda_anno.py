from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission, require_superuser
from app.core.database import get_db
from app.exceptions.configurazione_banda_anno import (
    AnnoGiaApertoError,
    AnnoGiaChiusoError,
    ConfigurazioneBandaAnnoChiusaError,
    ConfigurazioneBandaAnnoDuplicateError,
    ConfigurazioneBandaAnnoNotFoundError,
    RendicontoLookupNotFoundError,
)
from app.models.utente import Utente
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.schemas.configurazione_banda_anno import (
    ConfigurazioneBandaAnnoCreate,
    ConfigurazioneBandaAnnoResponse,
    ConfigurazioneBandaAnnoUpdate,
)
from app.services.configurazione_banda_anno_service import (
    ConfigurazioneBandaAnnoService,
)

router = APIRouter(
    prefix="/configurazione-banda-anno",
    tags=["configurazione-banda-anno"],
)


def get_service(db: AsyncSession = Depends(get_db)) -> ConfigurazioneBandaAnnoService:
    return ConfigurazioneBandaAnnoService(ConfigurazioneBandaAnnoRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[ConfigurazioneBandaAnnoResponse],
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def list_configurazioni(
    banda_codice: int | None = None,
    anno: int | None = None,
    params: PageParams = Depends(),
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> PagedResponse[ConfigurazioneBandaAnnoResponse]:
    return await service.get_all(banda_codice, anno, params)


@router.get(
    "/banda/{banda_codice}/anno/{anno}",
    response_model=ConfigurazioneBandaAnnoResponse,
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def get_by_banda_anno(
    banda_codice: int,
    anno: int,
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.get_by_banda_anno(banda_codice, anno)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get(
    "/{cfg_id}",
    response_model=ConfigurazioneBandaAnnoResponse,
    dependencies=[Depends(require_permission("contabilita:read"))],
)
async def get_configurazione(
    cfg_id: int,
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.get_by_id(cfg_id)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=ConfigurazioneBandaAnnoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("contabilita:write"))],
)
async def create_configurazione(
    data: ConfigurazioneBandaAnnoCreate,
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.create(data)
    except ConfigurazioneBandaAnnoDuplicateError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
    except RendicontoLookupNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.patch(
    "/{cfg_id}",
    response_model=ConfigurazioneBandaAnnoResponse,
    dependencies=[Depends(require_permission("contabilita:write"))],
)
async def update_configurazione(
    cfg_id: int,
    data: ConfigurazioneBandaAnnoUpdate,
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.update(cfg_id, data)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConfigurazioneBandaAnnoChiusaError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{cfg_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("contabilita:write"))],
)
async def delete_configurazione(
    cfg_id: int,
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> None:
    try:
        await service.delete(cfg_id)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ConfigurazioneBandaAnnoChiusaError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post(
    "/{cfg_id}/chiudi",
    response_model=ConfigurazioneBandaAnnoResponse,
)
async def chiudi_anno(
    cfg_id: int,
    current_user: Utente = Depends(require_permission("contabilita:write")),
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.chiudi_anno(cfg_id, current_user.id)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AnnoGiaChiusoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.post(
    "/{cfg_id}/riapri",
    response_model=ConfigurazioneBandaAnnoResponse,
)
async def riapri_anno(
    cfg_id: int,
    _: Utente = Depends(require_superuser),
    service: ConfigurazioneBandaAnnoService = Depends(get_service),
) -> ConfigurazioneBandaAnnoResponse:
    try:
        return await service.riapri_anno(cfg_id)
    except ConfigurazioneBandaAnnoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except AnnoGiaApertoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
