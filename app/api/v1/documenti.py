from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.storage import file_exists
from app.exceptions.documento import (
    DocumentoNotFoundError,
    DocumentoSottoCartellaNotFoundError,
    DocumentoTipoNonValidoError,
)
from app.models.utente import Utente
from app.repositories.documento_repository import DocumentoRepository
from app.repositories.sotto_cartella_repository import (
    MacroSezioneRepository,
    SottoCartellaRepository,
)
from app.schemas.documento import DocumentoResponse
from app.services.documento_service import DocumentoService

router = APIRouter(prefix="/documenti", tags=["documenti"])


def get_service(db: AsyncSession = Depends(get_db)) -> DocumentoService:
    return DocumentoService(
        DocumentoRepository(db),
        SottoCartellaRepository(db),
        MacroSezioneRepository(db),
    )


@router.get("/", response_model=PagedResponse[DocumentoResponse])
async def list_documenti(
    tipo_documento_codice: int | None = Query(None),
    sotto_cartella_id: int | None = Query(None),
    params: PageParams = Depends(),
    user: Utente = Depends(get_current_user),
    service: DocumentoService = Depends(get_service),
) -> PagedResponse[DocumentoResponse]:
    try:
        return await service.get_all(
            tipo_documento_codice, params, user, sotto_cartella_id=sotto_cartella_id
        )
    except DocumentoSottoCartellaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{documento_id}", response_model=DocumentoResponse)
async def get_documento(
    # No RBAC gate: direct-by-ID access requires already knowing the ID;
    # gating single-doc reads is out of scope for this CR.
    documento_id: int,
    service: DocumentoService = Depends(get_service),
) -> DocumentoResponse:
    try:
        return await service.get_by_id(documento_id)
    except DocumentoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=DocumentoResponse, status_code=status.HTTP_201_CREATED)
async def upload_documento(
    file: UploadFile,
    tipo_documento_codice: int | None = Query(None),
    sotto_cartella_id: int | None = Query(None),
    note: str | None = Query(None),
    user: Utente = Depends(get_current_user),
    service: DocumentoService = Depends(get_service),
) -> DocumentoResponse:
    try:
        return await service.upload(
            file, user, tipo_documento_codice, sotto_cartella_id, note
        )
    except DocumentoTipoNonValidoError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e
    except DocumentoSottoCartellaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# download/preview share the same no-gate rationale as get_documento above.
async def _resolve_file(documento_id: int, service: DocumentoService):  # type: ignore[return]
    try:
        doc = await service.get_by_id(documento_id)
    except DocumentoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    if not await file_exists(doc.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato sul server"
        )
    return doc


@router.get("/{documento_id}/download")
async def download_documento(
    documento_id: int,
    service: DocumentoService = Depends(get_service),
) -> FileResponse:
    doc = await _resolve_file(documento_id, service)
    return FileResponse(path=doc.file_path, media_type=doc.mime_type, filename=doc.nome)


@router.get("/{documento_id}/preview")
async def preview_documento(
    documento_id: int,
    service: DocumentoService = Depends(get_service),
) -> FileResponse:
    doc = await _resolve_file(documento_id, service)
    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'inline; filename="{doc.nome}"'},
    )


@router.delete("/{documento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_documento(
    documento_id: int,
    user: Utente = Depends(get_current_user),
    service: DocumentoService = Depends(get_service),
) -> None:
    try:
        await service.delete(documento_id, user)
    except DocumentoNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except DocumentoSottoCartellaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
