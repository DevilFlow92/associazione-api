from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate
from fastapi import UploadFile

from app.core.storage import delete_file, save_upload, validate_pdf
from app.exceptions.template import TemplateNotFoundError, TemplateTipoNonValidoError
from app.models.template import TipoTemplate
from app.repositories.template_repository import TemplateRepository
from app.schemas.template import TemplateResponse, TemplateUpdate

MIME_TYPES_ACCETTATI = {"application/pdf"}


class TemplateService:
    def __init__(self, repo: TemplateRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        tipo: TipoTemplate | None,
        solo_attivi: bool,
        params: PageParams,
    ) -> PagedResponse[TemplateResponse]:
        templates = await self.repo.get_all(
            tipo=tipo, solo_attivi=solo_attivi, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(tipo=tipo, solo_attivi=solo_attivi)
        items = [TemplateResponse.model_validate(t) for t in templates]
        return paginate(items, total, params)

    async def get_by_id(self, template_id: int) -> TemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        return TemplateResponse.model_validate(template)

    async def upload(
        self,
        file: UploadFile,
        tipo: TipoTemplate,
        nome: str,
        descrizione: str | None = None,
    ) -> TemplateResponse:
        if file.content_type not in MIME_TYPES_ACCETTATI:
            raise TemplateTipoNonValidoError(file.content_type or "unknown")

        content = await file.read()
        if not validate_pdf(content):
            raise TemplateTipoNonValidoError(file.content_type or "unknown")

        await file.seek(0)
        file_path, checksum, dimensione = await save_upload(
            file,
            f"templates/{tipo.value}",
        )

        template = await self.repo.create(
            nome=nome,
            tipo=tipo,
            file_path=file_path,
            mime_type=file.content_type or "application/pdf",
            dimensione_bytes=dimensione,
            checksum=checksum,
            descrizione=descrizione,
        )
        return TemplateResponse.model_validate(template)

    async def update(self, template_id: int, data: TemplateUpdate) -> TemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        updated = await self.repo.update(template, data)
        return TemplateResponse.model_validate(updated)

    async def delete(self, template_id: int) -> None:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        delete_file(template.file_path)
        await self.repo.delete(template)
