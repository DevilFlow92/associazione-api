from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.template import TemplateNotFoundError
from app.repositories.template_repository import TemplateRepository
from app.schemas.documento import DocumentoResponse
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate


class TemplateService:
    def __init__(self, repo: TemplateRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        documento_id: int | None,
        params: PageParams,
    ) -> PagedResponse[TemplateResponse]:
        templates = await self.repo.get_all(
            documento_id=documento_id, offset=params.offset, limit=params.limit
        )
        total = await self.repo.count_all(documento_id=documento_id)
        items = [TemplateResponse.model_validate(t) for t in templates]
        return paginate(items, total, params)

    async def get_by_id(self, template_id: int) -> TemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        return TemplateResponse.model_validate(template)

    async def create(self, data: TemplateCreate) -> TemplateResponse:
        # documento_id inesistente → IntegrityError → 409 (handler globale).
        template = await self.repo.create(data)
        return TemplateResponse.model_validate(template)

    async def update(self, template_id: int, data: TemplateUpdate) -> TemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        updated = await self.repo.update(template, data)
        return TemplateResponse.model_validate(updated)

    async def get_documento_file(self, template_id: int) -> DocumentoResponse:
        """Documento (file) collegato al template, per il download."""
        template = await self.repo.get_with_documento(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        return DocumentoResponse.model_validate(template.documento)

    async def delete(self, template_id: int) -> None:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        # Il file appartiene al Documento: non viene cancellato qui.
        await self.repo.delete(template)
