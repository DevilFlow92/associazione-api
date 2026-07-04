from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import storage
from app.exceptions.template import TemplateNotFoundError
from app.mergefields.registry import resolve_context
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.template_repository import TemplateRepository
from app.schemas.documento import DocumentoResponse
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateUpdate
from app.services.render.docx_walker import build_docx
from app.services.render.html_renderer import build_html
from app.services.render.pdf_renderer import build_pdf

_DOCX_MIME_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
_PDF_MIME_TYPE = "application/pdf"


class TemplateService:
    def __init__(
        self, repo: TemplateRepository, documento_repo: DocumentoRepository
    ) -> None:
        self.repo = repo
        self.documento_repo = documento_repo

    async def get_all(self, params: PageParams) -> PagedResponse[TemplateResponse]:
        templates = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [TemplateResponse.model_validate(t) for t in templates]
        return paginate(items, total, params)

    async def get_by_id(self, template_id: int) -> TemplateResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)
        return TemplateResponse.model_validate(template)

    async def create(self, data: TemplateCreate) -> TemplateResponse:
        template = await self.repo.create(data)
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
        await self.repo.delete(template)

    async def generate_docx(
        self, template_id: int, entities: dict[str, int], db: AsyncSession
    ) -> DocumentoResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)

        context = await resolve_context(entities, db)
        content = build_docx(template.contenuto_json, context)

        filename = f"{template.nome}.docx"
        file_path, checksum, dimensione = await storage.save(
            content, "documenti/generati", filename
        )
        documento = await self.documento_repo.create(
            nome=filename,
            file_path=file_path,
            mime_type=_DOCX_MIME_TYPE,
            dimensione_bytes=dimensione,
            checksum=checksum,
        )
        return DocumentoResponse.model_validate(documento)

    async def generate_pdf(
        self, template_id: int, entities: dict[str, int], db: AsyncSession
    ) -> DocumentoResponse:
        template = await self.repo.get_by_id(template_id)
        if not template:
            raise TemplateNotFoundError(template_id)

        context = await resolve_context(entities, db)
        html = build_html(template.contenuto_json, context)
        content = await build_pdf(html)

        filename = f"{template.nome}.pdf"
        file_path, checksum, dimensione = await storage.save(
            content, "documenti/generati", filename
        )
        documento = await self.documento_repo.create(
            nome=filename,
            file_path=file_path,
            mime_type=_PDF_MIME_TYPE,
            dimensione_bytes=dimensione,
            checksum=checksum,
        )
        return DocumentoResponse.model_validate(documento)
