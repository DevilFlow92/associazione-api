from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.template import TemplateNotFoundError
from app.repositories.template_repository import TemplateRepository
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


def get_service(db: AsyncSession = Depends(get_db)) -> TemplateService:
    return TemplateService(TemplateRepository(db))


@router.get(
    "/",
    response_model=PagedResponse[TemplateResponse],
    dependencies=[Depends(require_permission("templates:read"))],
)
async def list_templates(
    params: PageParams = Depends(),
    service: TemplateService = Depends(get_service),
) -> PagedResponse[TemplateResponse]:
    return await service.get_all(params)


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    dependencies=[Depends(require_permission("templates:read"))],
)
async def get_template(
    template_id: int,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    try:
        return await service.get_by_id(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post(
    "/",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("templates:write"))],
)
async def create_template(
    data: TemplateCreate,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    return await service.create(data)


@router.patch(
    "/{template_id}",
    response_model=TemplateResponse,
    dependencies=[Depends(require_permission("templates:write"))],
)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    try:
        return await service.update(template_id, data)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_permission("templates:write"))],
)
async def delete_template(
    template_id: int,
    service: TemplateService = Depends(get_service),
) -> None:
    try:
        await service.delete(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
