import io
import json
import zipfile

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.storage import storage
from app.exceptions.committente import CommittenteNotFoundError
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.libretto import (
    PersonaNonInOrganicoError,
    ServizioSenzaOrganicoError,
    ServizioSenzaRepertorioError,
)
from app.exceptions.servizio import ServizioHasRicevuteError, ServizioNotFoundError
from app.repositories.committente_repository import CommittenteRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.repertorio_item_repository import RepertorioItemRepository
from app.repositories.servizio_repository import ServizioRepository
from app.schemas.servizio import ServizioCreate, ServizioResponse, ServizioUpdate
from app.services.libretto_service import LibrettoPersona, LibrettoService
from app.services.servizio_service import ServizioService

router = APIRouter(prefix="/servizi", tags=["servizi"])


def get_service(db: AsyncSession = Depends(get_db)) -> ServizioService:
    return ServizioService(
        ServizioRepository(db), IndirizzoRepository(db), CommittenteRepository(db)
    )


def get_libretto_service(db: AsyncSession = Depends(get_db)) -> LibrettoService:
    return LibrettoService(
        ServizioRepository(db),
        PresenzaRepository(db),
        RepertorioItemRepository(db),
        storage,
    )


def _nome_file_persona(libretto: LibrettoPersona) -> str:
    parti = [p for p in (libretto.cognome, libretto.nome) if p]
    base = "_".join(parti) if parti else f"persona_{libretto.persona_id}"
    sicuro = "".join(c for c in base if c.isalnum() or c in (" ", "_", "-"))
    return sicuro.replace(" ", "_") or f"persona_{libretto.persona_id}"


@router.get("/", response_model=PagedResponse[ServizioResponse])
async def list_servizi(
    anno: int | None = None,
    banda_codice: int | None = Query(None),
    params: PageParams = Depends(),
    service: ServizioService = Depends(get_service),
) -> PagedResponse[ServizioResponse]:
    return await service.get_all(anno, params, banda_codice=banda_codice)


@router.get("/{servizio_id}", response_model=ServizioResponse)
async def get_servizio(
    servizio_id: int, service: ServizioService = Depends(get_service)
) -> ServizioResponse:
    try:
        return await service.get_by_id(servizio_id)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=ServizioResponse, status_code=status.HTTP_201_CREATED)
async def create_servizio(
    data: ServizioCreate, service: ServizioService = Depends(get_service)
) -> ServizioResponse:
    try:
        return await service.create(data)
    except (IndirizzoNotFoundError, CommittenteNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/{servizio_id}", response_model=ServizioResponse)
async def update_servizio(
    servizio_id: int,
    data: ServizioUpdate,
    service: ServizioService = Depends(get_service),
) -> ServizioResponse:
    try:
        return await service.update(servizio_id, data)
    except (
        ServizioNotFoundError,
        IndirizzoNotFoundError,
        CommittenteNotFoundError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{servizio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_servizio(
    servizio_id: int, service: ServizioService = Depends(get_service)
) -> None:
    try:
        await service.delete(servizio_id)
    except ServizioNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ServizioHasRicevuteError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get("/{servizio_id}/libretto")
async def get_libretto(
    servizio_id: int,
    persona_id: int | None = Query(
        None, description="Genera il libretto di una sola persona in organico"
    ),
    service: LibrettoService = Depends(get_libretto_service),
) -> Response:
    """Libretto PDF del servizio: le parti di ciascuna persona in organico
    per i brani del repertorio, nell'ordine del programma.

    Con ``persona_id`` restituisce il PDF della singola persona (eventuali
    brani mancanti sono segnalati nell'header ``X-Brani-Mancanti``); senza,
    restituisce uno ZIP con un PDF per persona più un ``report.json`` che
    elenca, per ciascuna, i brani mancanti o l'assenza totale di spartiti.
    """
    try:
        risultati = await service.build(servizio_id, persona_id)
    except (
        ServizioNotFoundError,
        ServizioSenzaOrganicoError,
        ServizioSenzaRepertorioError,
        PersonaNonInOrganicoError,
    ) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    if persona_id is not None:
        libretto = risultati[0]
        if libretto.pdf_bytes is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=(
                    f"Nessuno spartito trovato per la persona {persona_id} "
                    f"nel servizio {servizio_id}"
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

    # Organico completo: uno ZIP con un PDF per persona + un report.json che
    # segnala esplicitamente brani mancanti e persone senza alcuno spartito.
    buffer = io.BytesIO()
    report: dict = {"servizio_id": servizio_id, "persone": []}
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
                f'attachment; filename="libretto_servizio_{servizio_id}.zip"'
            )
        },
    )
