from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_permission
from app.core.database import get_db
from app.exceptions.esterno import EsternoNotFoundError
from app.exceptions.socio import SocioNotFoundError
from app.exceptions.template import TemplateNotFoundError, TemplateRenderError
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.template_repository import TemplateRepository
from app.schemas.documento import DocumentoResponse
from app.schemas.template import (
    TemplateCreate,
    TemplateGenerateRequest,
    TemplateResponse,
    TemplateUpdate,
)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


def get_service(db: AsyncSession = Depends(get_db)) -> TemplateService:
    return TemplateService(TemplateRepository(db), DocumentoRepository(db))


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


@router.post(
    "/{template_id}/generate/docx",
    response_model=DocumentoResponse,
    dependencies=[Depends(require_permission("templates:read"))],
)
async def generate_template_docx(
    template_id: int,
    data: TemplateGenerateRequest,
    db: AsyncSession = Depends(get_db),
    service: TemplateService = Depends(get_service),
) -> DocumentoResponse:
    try:
        return await service.generate_docx(template_id, data.entities, db)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (SocioNotFoundError, EsternoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entità sconosciuta: {e}",
        ) from e
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.post(
    "/{template_id}/generate/pdf",
    response_model=DocumentoResponse,
    dependencies=[Depends(require_permission("templates:read"))],
)
async def generate_template_pdf(
    template_id: int,
    data: TemplateGenerateRequest,
    db: AsyncSession = Depends(get_db),
    service: TemplateService = Depends(get_service),
) -> DocumentoResponse:
    try:
        return await service.generate_pdf(template_id, data.entities, db)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except (SocioNotFoundError, EsternoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Entità sconosciuta: {e}",
        ) from e
    except TemplateRenderError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
