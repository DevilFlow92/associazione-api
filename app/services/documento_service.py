from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate
from fastapi import UploadFile

from app.core.storage import delete_file, save_upload, validate_pdf
from app.exceptions.documento import DocumentoNotFoundError, DocumentoTipoNonValidoError
from app.repositories.documento_repository import DocumentoRepository
from app.schemas.documento import DocumentoResponse

MIME_TYPES_ACCETTATI = {"application/pdf"}


class DocumentoService:
    def __init__(self, repo: DocumentoRepository) -> None:
        self.repo = repo

    async def get_all(
        self,
        tipo_documento_codice: int | None,
        params: PageParams,
    ) -> PagedResponse[DocumentoResponse]:
        documenti = await self.repo.get_all(
            tipo_documento_codice=tipo_documento_codice,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(tipo_documento_codice=tipo_documento_codice)
        items = [DocumentoResponse.model_validate(d) for d in documenti]
        return paginate(items, total, params)

    async def get_by_id(self, documento_id: int) -> DocumentoResponse:
        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            raise DocumentoNotFoundError(documento_id)
        return DocumentoResponse.model_validate(documento)

    async def upload(
        self,
        file: UploadFile,
        tipo_documento_codice: int | None = None,
        note: str | None = None,
    ) -> DocumentoResponse:
        if file.content_type not in MIME_TYPES_ACCETTATI:
            raise DocumentoTipoNonValidoError(file.content_type or "unknown")

        content = await file.read()
        if not validate_pdf(content):
            raise DocumentoTipoNonValidoError(file.content_type or "unknown")

        await file.seek(0)
        sottocartella = (
            f"documenti/{tipo_documento_codice}"
            if tipo_documento_codice is not None
            else "documenti"
        )
        file_path, checksum, dimensione = await save_upload(file, sottocartella)

        documento = await self.repo.create(
            nome=file.filename or "documento.pdf",
            file_path=file_path,
            mime_type=file.content_type or "application/pdf",
            dimensione_bytes=dimensione,
            checksum=checksum,
            tipo_documento_codice=tipo_documento_codice,
            note=note,
        )
        return DocumentoResponse.model_validate(documento)

    async def delete(self, documento_id: int) -> None:
        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            raise DocumentoNotFoundError(documento_id)
        delete_file(documento.file_path)
        await self.repo.delete(documento)
