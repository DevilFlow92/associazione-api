"""Router della scheda alunno.

Due superfici distinte, deliberatamente NON fuse in un unico GET:

- ``/schede-alunno/...`` — CRUD del personale corsi, protetto dal solo RBAC
  resource:action (``corsi:read`` in lettura, ``corsi:write`` in scrittura),
  esattamente come gli altri router del progetto;
- ``/schede-alunno/me/{iscrizione_corso_id}`` — accesso dell'alunno alla
  propria scheda (lettura) e alle proprie autovalutazioni (scrittura, card
  #218), entrambe protette dal controllo row-level ma con perimetri diversi
  — vedi ``rbac_row_level``.

Un unico ``GET /schede-alunno/{id}`` che ospiti entrambe le logiche dovrebbe
concedere l'accesso a chiunque sia autenticato per poi negarlo dall'interno:
la guardia dichiarativa del router non potrebbe più esprimere il requisito, e
ogni futura modifica al corpo rischierebbe di aprire la lettura a tutti. Con
due percorsi separati ciascun endpoint ha una regola sola e leggibile, e
l'endpoint dell'alunno è indicizzato per ``iscrizione_corso_id`` — l'alunno
conosce la propria iscrizione, non l'id della scheda che non ha mai visto.
"""

from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.core.storage import StorageFileNotFoundError, storage
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import (
    AccessoSchedaAlunnoNegatoError,
    SchedaAlunnoDuplicataError,
    SchedaAlunnoIscrizioneNotFoundError,
    SchedaAlunnoNotFoundError,
)
from app.exceptions.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneNotFoundError,
)
from app.exceptions.scheda_alunno_materiale import (
    EstensioneMaterialeNonAmmessaError,
    MaterialeNonFileError,
    MaterialeTroppoGrandeError,
    SchedaAlunnoMaterialeNotFoundError,
)
from app.exceptions.scheda_alunno_voce import (
    SchedaAlunnoVoceNotFoundError,
    VoceCatalogoNonCompatibileError,
)
from app.exceptions.voce_programma_catalogo import VoceProgrammaCatalogoNotFoundError
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_autovalutazione_repository import (
    SchedaAlunnoAutovalutazioneRepository,
)
from app.repositories.scheda_alunno_materiale_repository import (
    SchedaAlunnoMaterialeRepository,
)
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.repositories.scheda_alunno_voce_repository import SchedaAlunnoVoceRepository
from app.repositories.scheda_alunno_voce_storico_repository import (
    SchedaAlunnoVoceStoricoRepository,
)
from app.repositories.voce_programma_catalogo_repository import (
    VoceProgrammaCatalogoRepository,
)
from app.schemas.scheda_alunno import (
    SchedaAlunnoCreate,
    SchedaAlunnoResponse,
    SchedaAlunnoUpdate,
)
from app.schemas.scheda_alunno_autovalutazione import (
    SchedaAlunnoAutovalutazioneCreate,
    SchedaAlunnoAutovalutazioneResponse,
    SchedaAlunnoAutovalutazioneUpdate,
)
from app.schemas.scheda_alunno_materiale import (
    SchedaAlunnoMaterialeLinkCreate,
    SchedaAlunnoMaterialeResponse,
)
from app.schemas.scheda_alunno_voce import (
    SchedaAlunnoVoceCreate,
    SchedaAlunnoVoceResponse,
    SchedaAlunnoVoceUpdate,
)
from app.schemas.scheda_alunno_voce_storico import SchedaAlunnoVoceStoricoResponse
from app.services.scheda_alunno_autovalutazione_service import (
    SchedaAlunnoAutovalutazioneService,
)
from app.services.scheda_alunno_materiale_service import SchedaAlunnoMaterialeService
from app.services.scheda_alunno_service import SchedaAlunnoService
from app.services.scheda_alunno_voce_service import SchedaAlunnoVoceService

router = APIRouter(prefix="/schede-alunno", tags=["schede-alunno"])


def get_service(db: AsyncSession = Depends(get_db)) -> SchedaAlunnoService:
    return SchedaAlunnoService(
        SchedaAlunnoRepository(db), IscrizioneCorsoRepository(db)
    )


def get_voci_service(db: AsyncSession = Depends(get_db)) -> SchedaAlunnoVoceService:
    return SchedaAlunnoVoceService(
        SchedaAlunnoVoceRepository(db),
        SchedaAlunnoRepository(db),
        IscrizioneCorsoRepository(db),
        VoceProgrammaCatalogoRepository(db),
        SchedaAlunnoVoceStoricoRepository(db),
    )


def get_materiali_service(
    db: AsyncSession = Depends(get_db),
) -> SchedaAlunnoMaterialeService:
    return SchedaAlunnoMaterialeService(
        SchedaAlunnoMaterialeRepository(db),
        SchedaAlunnoRepository(db),
        IscrizioneCorsoRepository(db),
    )


def get_autovalutazioni_service(
    db: AsyncSession = Depends(get_db),
) -> SchedaAlunnoAutovalutazioneService:
    return SchedaAlunnoAutovalutazioneService(
        SchedaAlunnoAutovalutazioneRepository(db),
        SchedaAlunnoRepository(db),
        IscrizioneCorsoRepository(db),
    )


def _forbidden(e: AccessoSchedaAlunnoNegatoError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


def _not_found(e: Exception) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ── Accesso dell'alunno alla propria scheda (row-level) ──────────────────────


@router.get("/me/{iscrizione_corso_id}", response_model=SchedaAlunnoResponse)
async def get_propria_scheda_alunno(
    iscrizione_corso_id: int,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    """Scheda dell'iscrizione indicata, se il chiamante ne ha titolo.

    Nessun permesso ``corsi:*`` richiesto — è il punto: l'alunno non ne ha.
    L'autorizzazione è interamente row-level (vedi ``rbac_row_level``).
    """
    try:
        return await service.get_propria_scheda(iscrizione_corso_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (IscrizioneCorsoNotFoundError, SchedaAlunnoIscrizioneNotFoundError) as e:
        raise _not_found(e) from e


# ── Autovalutazioni dell'alunno (row-level, scrittura concessa all'alunno) ──
#
# PRIMO caso nel progetto in cui l'alunno scrive, non solo legge, una riga
# della propria scheda — vedi ``assert_puo_scrivere_autovalutazione`` in
# ``rbac_row_level`` per il perimetro (deliberatamente più stretto di
# ``assert_puo_scrivere_scheda``: nessun bypass per chi ha ``corsi:write``,
# nemmeno per l'insegnante/coordinatore del corso specifico). Indicizzati per
# ``iscrizione_corso_id``, come ``GET /me/{iscrizione_corso_id}``, non per
# ``scheda_alunno_id``: l'alunno non ha mai visto l'id della scheda.


@router.post(
    "/me/{iscrizione_corso_id}/autovalutazioni",
    response_model=SchedaAlunnoAutovalutazioneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_autovalutazione(
    iscrizione_corso_id: int,
    data: SchedaAlunnoAutovalutazioneCreate,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoAutovalutazioneService = Depends(get_autovalutazioni_service),
) -> SchedaAlunnoAutovalutazioneResponse:
    try:
        return await service.create(iscrizione_corso_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (IscrizioneCorsoNotFoundError, SchedaAlunnoIscrizioneNotFoundError) as e:
        raise _not_found(e) from e


@router.patch(
    "/me/{iscrizione_corso_id}/autovalutazioni/{autovalutazione_id}",
    response_model=SchedaAlunnoAutovalutazioneResponse,
)
async def update_autovalutazione(
    iscrizione_corso_id: int,
    autovalutazione_id: int,
    data: SchedaAlunnoAutovalutazioneUpdate,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoAutovalutazioneService = Depends(get_autovalutazioni_service),
) -> SchedaAlunnoAutovalutazioneResponse:
    try:
        return await service.update(
            iscrizione_corso_id, autovalutazione_id, data, utente
        )
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoIscrizioneNotFoundError,
        SchedaAlunnoAutovalutazioneNotFoundError,
    ) as e:
        raise _not_found(e) from e


@router.delete(
    "/me/{iscrizione_corso_id}/autovalutazioni/{autovalutazione_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_autovalutazione(
    iscrizione_corso_id: int,
    autovalutazione_id: int,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoAutovalutazioneService = Depends(get_autovalutazioni_service),
) -> None:
    try:
        await service.delete(iscrizione_corso_id, autovalutazione_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoIscrizioneNotFoundError,
        SchedaAlunnoAutovalutazioneNotFoundError,
    ) as e:
        raise _not_found(e) from e


# ── CRUD del personale corsi ─────────────────────────────────────────────────


@router.get(
    "/",
    response_model=PagedResponse[SchedaAlunnoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def list_schede_alunno(
    iscrizione_corso_id: int | None = Query(None),
    params: PageParams = Depends(),
    service: SchedaAlunnoService = Depends(get_service),
) -> PagedResponse[SchedaAlunnoResponse]:
    return await service.get_all(params, iscrizione_corso_id=iscrizione_corso_id)


@router.get(
    "/{scheda_alunno_id}",
    response_model=SchedaAlunnoResponse,
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_scheda_alunno(
    scheda_alunno_id: int, service: SchedaAlunnoService = Depends(get_service)
) -> SchedaAlunnoResponse:
    try:
        return await service.get_by_id(scheda_alunno_id)
    except SchedaAlunnoNotFoundError as e:
        raise _not_found(e) from e


@router.post(
    "/", response_model=SchedaAlunnoResponse, status_code=status.HTTP_201_CREATED
)
async def create_scheda_alunno(
    data: SchedaAlunnoCreate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    try:
        return await service.create(data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except IscrizioneCorsoNotFoundError as e:
        raise _not_found(e) from e
    except SchedaAlunnoDuplicataError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.patch("/{scheda_alunno_id}", response_model=SchedaAlunnoResponse)
async def update_scheda_alunno(
    scheda_alunno_id: int,
    data: SchedaAlunnoUpdate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> SchedaAlunnoResponse:
    try:
        return await service.update(scheda_alunno_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e


@router.delete("/{scheda_alunno_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheda_alunno(
    scheda_alunno_id: int,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoService = Depends(get_service),
) -> None:
    try:
        await service.delete(scheda_alunno_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e


# ── Voci di programma della scheda ────────────────────────────────────────────
#
# Nessuna nuova regola di autorizzazione: le voci appartengono alla scheda,
# quindi la guardia dichiarativa è la stessa ``corsi:write``/``corsi:read``
# del resto di questo router, con lo stesso controllo row-level per-corso
# applicato dentro ``SchedaAlunnoVoceService`` (``assert_puo_scrivere_scheda``).
# La lettura delle voci non ha un endpoint proprio: arriva incorporata nella
# ``SchedaAlunnoResponse`` (campo ``voci``, già ordinato per ``ordine``).
#
# NOTA per revisione: il progetto ha già un pattern di PATCH bulk per liste
# (``PATCH /presenze/bulk`` in ``app/api/v1/presenze.py``). Non l'ho aggiunto
# qui: la card lo chiedeva solo come proposta da segnalare, non da
# implementare in sostituzione degli endpoint singoli. Se in pratica
# l'insegnante compone il programma di più voci in un'unica sessione, un
# ``PATCH /schede-alunno/{scheda_alunno_id}/voci/bulk`` per riordino/stato di
# più voci alla volta eviterebbe N round-trip — da valutare in una card a
# parte.


@router.post(
    "/{scheda_alunno_id}/voci",
    response_model=SchedaAlunnoVoceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_voce_scheda_alunno(
    scheda_alunno_id: int,
    data: SchedaAlunnoVoceCreate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoVoceService = Depends(get_voci_service),
) -> SchedaAlunnoVoceResponse:
    try:
        return await service.create(scheda_alunno_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        SchedaAlunnoNotFoundError,
        IscrizioneCorsoNotFoundError,
        VoceProgrammaCatalogoNotFoundError,
    ) as e:
        raise _not_found(e) from e
    except VoceCatalogoNonCompatibileError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.patch(
    "/{scheda_alunno_id}/voci/{voce_id}",
    response_model=SchedaAlunnoVoceResponse,
)
async def update_voce_scheda_alunno(
    scheda_alunno_id: int,
    voce_id: int,
    data: SchedaAlunnoVoceUpdate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoVoceService = Depends(get_voci_service),
) -> SchedaAlunnoVoceResponse:
    try:
        return await service.update(scheda_alunno_id, voce_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        SchedaAlunnoNotFoundError,
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoVoceNotFoundError,
    ) as e:
        raise _not_found(e) from e


@router.delete(
    "/{scheda_alunno_id}/voci/{voce_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_voce_scheda_alunno(
    scheda_alunno_id: int,
    voce_id: int,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoVoceService = Depends(get_voci_service),
) -> None:
    try:
        await service.delete(scheda_alunno_id, voce_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        SchedaAlunnoNotFoundError,
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoVoceNotFoundError,
    ) as e:
        raise _not_found(e) from e


# ── Storico dei cambi di stato delle voci (sola lettura, card #219) ─────────
#
# La raccolta dati è append-only da #214 (mai stata esposta prima). Nessuna
# scrittura qui: entrambi gli endpoint sono GET paginati, stesso
# ``PagedResponse``/``PageParams`` del resto del progetto.
#
# Superficie personale corsi: guardia ``corsi:read``, nessun controllo
# row-level aggiuntivo nel service — vedi il commento in
# ``SchedaAlunnoVoceService.get_storico`` per la deviazione dal testo della
# card #219 su questo punto.
# Superficie alunno: indicizzata per ``iscrizione_corso_id`` come
# ``GET /me/{iscrizione_corso_id}``, autorizzazione interamente row-level
# (``assert_puo_leggere_scheda``, riusata senza modifiche).


@router.get(
    "/{scheda_alunno_id}/storico-voci",
    response_model=PagedResponse[SchedaAlunnoVoceStoricoResponse],
    dependencies=[Depends(require_permission("corsi:read"))],
)
async def get_storico_voci_scheda_alunno(
    scheda_alunno_id: int,
    params: PageParams = Depends(),
    service: SchedaAlunnoVoceService = Depends(get_voci_service),
) -> PagedResponse[SchedaAlunnoVoceStoricoResponse]:
    try:
        return await service.get_storico(scheda_alunno_id, params)
    except SchedaAlunnoNotFoundError as e:
        raise _not_found(e) from e


@router.get(
    "/me/{iscrizione_corso_id}/storico-voci",
    response_model=PagedResponse[SchedaAlunnoVoceStoricoResponse],
)
async def get_proprio_storico_voci_scheda_alunno(
    iscrizione_corso_id: int,
    params: PageParams = Depends(),
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoVoceService = Depends(get_voci_service),
) -> PagedResponse[SchedaAlunnoVoceStoricoResponse]:
    try:
        return await service.get_proprio_storico(iscrizione_corso_id, params, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (IscrizioneCorsoNotFoundError, SchedaAlunnoIscrizioneNotFoundError) as e:
        raise _not_found(e) from e


# ── Materiale didattico della scheda ─────────────────────────────────────────
#
# Nessuna nuova regola di autorizzazione: la scrittura riusa esattamente
# ``corsi:write`` + ``assert_puo_scrivere_scheda``, stesso controllo delle
# voci. Il download è invece l'unico endpoint di QUESTO router che applica il
# row-level in lettura (``assert_puo_leggere_scheda``, non la guardia
# dichiarativa ``corsi:read``): a differenza delle voci un materiale-file va
# scaricato anche dall'alunno proprietario, che non ha mai ``corsi:read``.


@router.post(
    "/{scheda_alunno_id}/materiali/file",
    response_model=SchedaAlunnoMaterialeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_materiale_scheda_alunno(
    scheda_alunno_id: int,
    titolo: str = Form(...),
    file: UploadFile = File(...),
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoMaterialeService = Depends(get_materiali_service),
) -> SchedaAlunnoMaterialeResponse:
    try:
        return await service.upload_file(scheda_alunno_id, titolo, file, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e
    except (EstensioneMaterialeNonAmmessaError, MaterialeTroppoGrandeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e


@router.post(
    "/{scheda_alunno_id}/materiali/link",
    response_model=SchedaAlunnoMaterialeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def crea_materiale_link_scheda_alunno(
    scheda_alunno_id: int,
    data: SchedaAlunnoMaterialeLinkCreate,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoMaterialeService = Depends(get_materiali_service),
) -> SchedaAlunnoMaterialeResponse:
    try:
        return await service.create_link(scheda_alunno_id, data, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (SchedaAlunnoNotFoundError, IscrizioneCorsoNotFoundError) as e:
        raise _not_found(e) from e


@router.get("/{scheda_alunno_id}/materiali/{materiale_id}/download")
async def download_materiale_scheda_alunno(
    scheda_alunno_id: int,
    materiale_id: int,
    utente: Utente = Depends(get_current_user),
    service: SchedaAlunnoMaterialeService = Depends(get_materiali_service),
) -> Response:
    try:
        materiale = await service.get_for_download(
            scheda_alunno_id, materiale_id, utente
        )
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        SchedaAlunnoNotFoundError,
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoMaterialeNotFoundError,
    ) as e:
        raise _not_found(e) from e
    except MaterialeNonFileError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        ) from e

    assert materiale.storage_key is not None  # garantito da get_for_download
    try:
        content = await storage.get_bytes(materiale.storage_key)
    except StorageFileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato sul server"
        )
    return Response(
        content=content,
        media_type=materiale.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": (
                f'attachment; filename="{materiale.nome_file_originale}"'
            )
        },
    )


@router.delete(
    "/{scheda_alunno_id}/materiali/{materiale_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_materiale_scheda_alunno(
    scheda_alunno_id: int,
    materiale_id: int,
    utente: Utente = Depends(require_permission("corsi:write")),
    service: SchedaAlunnoMaterialeService = Depends(get_materiali_service),
) -> None:
    try:
        await service.delete(scheda_alunno_id, materiale_id, utente)
    except AccessoSchedaAlunnoNegatoError as e:
        raise _forbidden(e) from e
    except (
        SchedaAlunnoNotFoundError,
        IscrizioneCorsoNotFoundError,
        SchedaAlunnoMaterialeNotFoundError,
    ) as e:
        raise _not_found(e) from e
