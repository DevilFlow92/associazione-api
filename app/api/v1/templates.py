from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import file_exists
from app.exceptions.template import TemplateNotFoundError
from app.repositories.template_repository import TemplateRepository
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["templates"])


def get_service(db: AsyncSession = Depends(get_db)) -> TemplateService:
    return TemplateService(TemplateRepository(db))


@router.get("/", response_model=PagedResponse[TemplateResponse])
async def list_templates(
    documento_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: TemplateService = Depends(get_service),
) -> PagedResponse[TemplateResponse]:
    return await service.get_all(documento_id, params)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    try:
        return await service.get_by_id(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    return await service.create(data)


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int,
    data: TemplateUpdate,
    service: TemplateService = Depends(get_service),
) -> TemplateResponse:
    try:
        return await service.update(template_id, data)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{template_id}/download")
async def download_template(
    template_id: int,
    service: TemplateService = Depends(get_service),
) -> FileResponse:
    try:
        doc = await service.get_documento_file(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if not await file_exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato sul server"
        )
    return FileResponse(path=doc.file_path, media_type=doc.mime_type, filename=doc.nome)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: int,
    service: TemplateService = Depends(get_service),
) -> None:
    try:
        await service.delete(template_id)
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
