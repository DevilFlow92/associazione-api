from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate
from fastapi import HTTPException, UploadFile, status

from app.core.storage import delete_file, save_upload
from app.exceptions.documento import (
    DocumentoNotFoundError,
    DocumentoSottoCartellaNotFoundError,
)
from app.models.macro_sezione import MacroSezione
from app.models.utente import Utente
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.sotto_cartella_repository import (
    MacroSezioneRepository,
    SottoCartellaRepository,
)
from app.schemas.documento import DocumentoResponse
from app.services.permessi_archivio import require_read, require_write


class DocumentoService:
    def __init__(
        self,
        repo: DocumentoRepository,
        sotto_cartella_repo: SottoCartellaRepository,
        macro_sezione_repo: MacroSezioneRepository,
    ) -> None:
        self.repo = repo
        self.sotto_cartella_repo = sotto_cartella_repo
        self.macro_sezione_repo = macro_sezione_repo

    async def _resolve_macro_sezione_for_sotto_cartella(
        self, sotto_cartella_id: int
    ) -> MacroSezione:
        sotto_cartella = await self.sotto_cartella_repo.get_by_id(sotto_cartella_id)
        if not sotto_cartella:
            raise DocumentoSottoCartellaNotFoundError(sotto_cartella_id)
        macro_sezione = await self.macro_sezione_repo.get_by_codice(
            sotto_cartella.macro_sezione_codice
        )
        if not macro_sezione:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Macro-sezione non trovata: integrità dati compromessa",
            )
        return macro_sezione

    async def get_all(
        self,
        tipo_documento_codice: int | None,
        params: PageParams,
        user: Utente,
        sotto_cartella_id: int | None = None,
    ) -> PagedResponse[DocumentoResponse]:
        if sotto_cartella_id is not None:
            macro_sezione = await self._resolve_macro_sezione_for_sotto_cartella(
                sotto_cartella_id
            )
            require_read(user, macro_sezione)
        documenti = await self.repo.get_all(
            tipo_documento_codice=tipo_documento_codice,
            sotto_cartella_id=sotto_cartella_id,
            offset=params.offset,
            limit=params.limit,
        )
        total = await self.repo.count_all(
            tipo_documento_codice=tipo_documento_codice,
            sotto_cartella_id=sotto_cartella_id,
        )
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
        user: Utente,
        tipo_documento_codice: int | None = None,
        sotto_cartella_id: int | None = None,
        note: str | None = None,
    ) -> DocumentoResponse:
        # Tutti i formati sono accettati. La validazione del tipo è
        # responsabilità del client. File eseguibili (.exe, .bat, ecc.)
        # non sono bloccati a livello di backend ma dovrebbero essere
        # filtrati dal frontend tramite l'attributo `accept`.
        if sotto_cartella_id is not None:
            macro_sezione = await self._resolve_macro_sezione_for_sotto_cartella(
                sotto_cartella_id
            )
            require_write(user, macro_sezione)

        sottocartella = (
            f"documenti/{tipo_documento_codice}"
            if tipo_documento_codice is not None
            else "documenti"
        )
        file_path, checksum, dimensione = await save_upload(file, sottocartella)

        documento = await self.repo.create(
            nome=file.filename or "documento",
            file_path=file_path,
            mime_type=file.content_type or "application/octet-stream",
            dimensione_bytes=dimensione,
            checksum=checksum,
            tipo_documento_codice=tipo_documento_codice,
            sotto_cartella_id=sotto_cartella_id,
            note=note,
        )
        return DocumentoResponse.model_validate(documento)

    async def delete(self, documento_id: int, user: Utente) -> None:
        documento = await self.repo.get_by_id(documento_id)
        if not documento:
            raise DocumentoNotFoundError(documento_id)
        if documento.sotto_cartella_id is not None:
            macro_sezione = await self._resolve_macro_sezione_for_sotto_cartella(
                documento.sotto_cartella_id
            )
            require_write(user, macro_sezione)
        await delete_file(documento.file_path)
        await self.repo.delete(documento)
