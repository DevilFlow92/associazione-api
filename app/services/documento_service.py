from __future__ import annotations

from fastapi import UploadFile

from app.core.storage import delete_file, save_upload, validate_pdf
from app.exceptions.documento import DocumentoNotFoundError, DocumentoTipoNonValidoError
from app.models.documento import TipoDocumento
from app.repositories.documento_repository import DocumentoRepository
from app.schemas.documento import DocumentoResponse

MIME_TYPES_ACCETTATI = {"application/pdf"}


class DocumentoService:
    def __init__(self, repo: DocumentoRepository) -> None:
        self.repo = repo

    async def get_all(
        self, tipo: TipoDocumento | None = None
    ) -> list[DocumentoResponse]:
        documenti = await self.repo.get_all(tipo)
        return [DocumentoResponse.model_validate(d) for d in documenti]

    async def get_by_id(self, documento_id: int) -> DocumentoResponse:
        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            raise DocumentoNotFoundError(documento_id)
        return DocumentoResponse.model_validate(documento)

    async def get_by_socio(self, socio_id: int) -> list[DocumentoResponse]:
        documenti = await self.repo.get_by_socio(socio_id)
        return [DocumentoResponse.model_validate(d) for d in documenti]

    async def upload(
        self,
        file: UploadFile,
        tipo: TipoDocumento,
        socio_id: int | None = None,
        note: str | None = None,
    ) -> DocumentoResponse:
        if file.content_type not in MIME_TYPES_ACCETTATI:
            raise DocumentoTipoNonValidoError(file.content_type or "unknown")

        content = await file.read()
        if not validate_pdf(content):
            raise DocumentoTipoNonValidoError(file.content_type or "unknown")

        await file.seek(0)
        file_path, checksum, dimensione = await save_upload(file, tipo.value)

        documento = await self.repo.create(
            nome=file.filename or "documento.pdf",
            tipo=tipo,
            file_path=file_path,
            mime_type=file.content_type or "application/pdf",
            dimensione_bytes=dimensione,
            checksum=checksum,
            socio_id=socio_id,
            note=note,
        )
        return DocumentoResponse.model_validate(documento)

    async def delete(self, documento_id: int) -> None:
        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            raise DocumentoNotFoundError(documento_id)
        delete_file(documento.file_path)
        await self.repo.delete(documento)
