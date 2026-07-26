import io
import json
import zipfile

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import storage
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.libretto import (
    PersonaNonInOrganicoProvaError,
    ProvaSenzaOrganicoError,
    ProvaSenzaRepertorioError,
)
from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.repertorio_item_repository import RepertorioItemRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.prova import ProvaCreate, ProvaResponse, ProvaUpdate
from app.services.libretto_service import LibrettoPersona, LibrettoService
from app.services.prova_service import ProvaService

router = APIRouter(prefix="/prove", tags=["prove"])


def get_service(db: AsyncSession = Depends(get_db)) -> ProvaService:
    return ProvaService(
        ProvaRepository(db), IndirizzoRepository(db), ServizioRepository(db)
    )


def get_libretto_service(db: AsyncSession = Depends(get_db)) -> LibrettoService:
    return LibrettoService(
        ServizioRepository(db),
        ProvaRepository(db),
        PresenzaRepository(db),
        RepertorioItemRepository(db),
        storage,
    )


def _nome_file_persona(libretto: LibrettoPersona) -> str:
    parti = [p for p in (libretto.cognome, libretto.nome) if p]
    base = "_".join(parti) if parti else f"persona_{libretto.persona_id}"
    sicuro = "".join(c for c in base if c.isalnum() or c in (" ", "_", "-"))
    return sicuro.replace(" ", "_") or f"persona_{libretto.persona_id}"


@router.get("/", response_model=PagedResponse[ProvaResponse])
async def list_prove(
    banda_codice: int | None = Query(None),
    servizio_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: ProvaService = Depends(get_service),
) -> PagedResponse[ProvaResponse]:
    return await service.get_all(
        params, banda_codice=banda_codice, servizio_id=servizio_id
    )


@router.get("/{prova_id}", response_model=ProvaResponse)
async def get_prova(
    prova_id: int, service: ProvaService = Depends(get_service)
) -> ProvaResponse:
    try:
        return await service.get_by_id(prova_id)
    except ProvaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=ProvaResponse, status_code=status.HTTP_201_CREATED)
async def create_prova(
    data: ProvaCreate, service: ProvaService = Depends(get_service)
) -> ProvaResponse:
    try:
        return await service.create(data)
    except (IndirizzoNotFoundError, ServizioNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{prova_id}", response_model=ProvaResponse)
async def update_prova(
    prova_id: int,
    data: ProvaUpdate,
    service: ProvaService = Depends(get_service),
) -> ProvaResponse:
    try:
        return await service.update(prova_id, data)
    except (ProvaNotFoundError, IndirizzoNotFoundError, ServizioNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{prova_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prova(
    prova_id: int, service: ProvaService = Depends(get_service)
) -> None:
    try:
        await service.delete(prova_id)
    except ProvaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.get("/{prova_id}/libretto")
async def get_libretto(
    prova_id: int,
    persona_id: int | None = Query(
        None, description="Genera il libretto di una sola persona in organico"
    ),
    service: LibrettoService = Depends(get_libretto_service),
) -> Response:
    """Libretto PDF della prova: stessa logica del libretto di Servizio,
    riusando organico (Presenza) e repertorio (RepertorioItem) con prova_id."""
    try:
        risultati = await service.build(prova_id=prova_id, persona_id=persona_id)
    except (
        ProvaNotFoundError,
        ProvaSenzaOrganicoError,
        ProvaSenzaRepertorioError,
        PersonaNonInOrganicoProvaError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if persona_id is not None:
        libretto = risultati[0]
        if libretto.pdf_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Nessuno spartito trovato per la persona {persona_id} "
                    f"nella prova {prova_id}"
                ),
            )
        headers = {
            "Content-Disposition": (
                f'attachment; filename="libretto_{_nome_file_persona(libretto)}.pdf"'
            )
        }
        if libretto.brani_mancanti:
            headers["X-Brani-Mancanti"] = "; ".join(
                b.nome_parte_nome for b in libretto.brani_mancanti
            )
        return Response(
            content=libretto.pdf_bytes,
            media_type="application/pdf",
            headers=headers,
        )

    buffer = io.BytesIO()
    report: dict = {"prova_id": prova_id, "persone": []}
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for libretto in risultati:
            voce = {
                "persona_id": libretto.persona_id,
                "nome": libretto.nome,
                "cognome": libretto.cognome,
                "strumento_indeterminato": libretto.strumento_indeterminato,
                "brani_mancanti": [b.nome_parte_nome for b in libretto.brani_mancanti],
            }
            if libretto.pdf_bytes is not None:
                nome_file = f"{_nome_file_persona(libretto)}.pdf"
                zf.writestr(nome_file, libretto.pdf_bytes)
                voce["file"] = nome_file
            else:
                voce["file"] = None
                voce["errore"] = "nessuno spartito trovato"
            report["persone"].append(voce)
        zf.writestr("report.json", json.dumps(report, indent=2, ensure_ascii=False))

    return Response(
        content=buffer.getvalue(),
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="libretto_prova_{prova_id}.zip"'
            )
        },
    )
