from __future__ import annotations

from pathlib import Path

from fastapi import UploadFile

from app.core.storage import storage
from app.exceptions.iscrizione_corso import IscrizioneCorsoNotFoundError
from app.exceptions.scheda_alunno import SchedaAlunnoNotFoundError
from app.exceptions.scheda_alunno_materiale import (
    EstensioneMaterialeNonAmmessaError,
    MaterialeNonFileError,
    MaterialeTroppoGrandeError,
    SchedaAlunnoMaterialeNotFoundError,
)
from app.models.iscrizione_corso import IscrizioneCorso
from app.models.scheda_alunno import SchedaAlunno
from app.models.scheda_alunno_materiale import SchedaAlunnoMateriale
from app.models.utente import Utente
from app.repositories.iscrizione_corso_repository import IscrizioneCorsoRepository
from app.repositories.scheda_alunno_materiale_repository import (
    SchedaAlunnoMaterialeRepository,
)
from app.repositories.scheda_alunno_repository import SchedaAlunnoRepository
from app.schemas.scheda_alunno_materiale import (
    SchedaAlunnoMaterialeLinkCreate,
    SchedaAlunnoMaterialeResponse,
)
from app.services.rbac_row_level import (
    assert_puo_leggere_scheda,
    assert_puo_scrivere_scheda,
)

# Validata sull'ESTENSIONE del nome file, non sul mime-type dichiarato dal
# client: alcuni formati (.mscz/.sib) non hanno un mime-type standard
# affidabile, l'estensione è l'unico segnale stabile lato client.
ESTENSIONI_AMMESSE = frozenset(
    {
        "pdf",
        "docx",
        "jpg",
        "jpeg",
        "png",
        "mp3",
        "m4a",
        "wav",
        "avi",
        "mp4",
        "mscz",
        "sib",
    }
)
DIMENSIONE_MASSIMA_BYTES = 20 * 1024 * 1024


class SchedaAlunnoMaterialeService:
    """CRUD del materiale didattico allegato a una scheda alunno.

    Nessuna nuova regola di autorizzazione: riusa integralmente
    ``assert_puo_scrivere_scheda``/``assert_puo_leggere_scheda`` risalendo
    scheda -> iscrizione_corso -> corso (per la scrittura) o -> persona_id
    (per la lettura), stesso pattern di ``SchedaAlunnoVoceService`` e
    ``SchedaAlunnoService.get_propria_scheda``.

    A differenza delle voci, qui non c'è uno storico da preservare: la
    cancellazione è un hard delete che, per i materiali di tipo file, rimuove
    anche l'oggetto su storage (nessun file orfano).
    """

    def __init__(
        self,
        repo: SchedaAlunnoMaterialeRepository,
        scheda_repo: SchedaAlunnoRepository,
        iscrizione_corso_repo: IscrizioneCorsoRepository,
    ) -> None:
        self.repo = repo
        self.scheda_repo = scheda_repo
        self.iscrizione_corso_repo = iscrizione_corso_repo

    async def _scheda_e_iscrizione(
        self, scheda_alunno_id: int
    ) -> tuple[SchedaAlunno, IscrizioneCorso]:
        scheda = await self.scheda_repo.get_by_id(scheda_alunno_id)
        if not scheda:
            raise SchedaAlunnoNotFoundError(scheda_alunno_id)
        iscrizione = await self.iscrizione_corso_repo.get_by_id(
            scheda.iscrizione_corso_id
        )
        if not iscrizione:
            raise IscrizioneCorsoNotFoundError(scheda.iscrizione_corso_id)
        return scheda, iscrizione

    async def _materiale_di_scheda(
        self, scheda_alunno_id: int, materiale_id: int
    ) -> SchedaAlunnoMateriale:
        materiale = await self.repo.get_by_id(materiale_id)
        if not materiale or materiale.scheda_alunno_id != scheda_alunno_id:
            raise SchedaAlunnoMaterialeNotFoundError(materiale_id)
        return materiale

    async def upload_file(
        self,
        scheda_alunno_id: int,
        titolo: str,
        file: UploadFile,
        utente: Utente,
    ) -> SchedaAlunnoMaterialeResponse:
        scheda, iscrizione = await self._scheda_e_iscrizione(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)

        nome_file = file.filename or ""
        estensione = Path(nome_file).suffix.removeprefix(".").lower()
        if estensione not in ESTENSIONI_AMMESSE:
            raise EstensioneMaterialeNonAmmessaError(estensione, ESTENSIONI_AMMESSE)

        content = await file.read()
        if len(content) > DIMENSIONE_MASSIMA_BYTES:
            raise MaterialeTroppoGrandeError(len(content), DIMENSIONE_MASSIMA_BYTES)

        storage_key, _checksum, dimensione = await storage.save(
            content, f"schede-alunno/{scheda_alunno_id}", nome_file
        )

        materiale = SchedaAlunnoMateriale(
            scheda_alunno_id=scheda_alunno_id,
            titolo=titolo,
            storage_key=storage_key,
            nome_file_originale=nome_file,
            mime_type=file.content_type,
            dimensione_bytes=dimensione,
            caricato_da_persona_id=utente.persona_id,
        )
        created = await self.repo.create(materiale)
        self.scheda_repo.expire(scheda)
        return SchedaAlunnoMaterialeResponse.model_validate(created)

    async def create_link(
        self,
        scheda_alunno_id: int,
        data: SchedaAlunnoMaterialeLinkCreate,
        utente: Utente,
    ) -> SchedaAlunnoMaterialeResponse:
        scheda, iscrizione = await self._scheda_e_iscrizione(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)

        materiale = SchedaAlunnoMateriale(
            scheda_alunno_id=scheda_alunno_id,
            titolo=data.titolo,
            url=data.url,
            caricato_da_persona_id=utente.persona_id,
        )
        created = await self.repo.create(materiale)
        self.scheda_repo.expire(scheda)
        return SchedaAlunnoMaterialeResponse.model_validate(created)

    async def get_for_download(
        self, scheda_alunno_id: int, materiale_id: int, utente: Utente
    ) -> SchedaAlunnoMateriale:
        _scheda, iscrizione = await self._scheda_e_iscrizione(scheda_alunno_id)
        assert_puo_leggere_scheda(utente, iscrizione.persona_id)
        materiale = await self._materiale_di_scheda(scheda_alunno_id, materiale_id)
        if materiale.storage_key is None:
            raise MaterialeNonFileError(materiale_id)
        return materiale

    async def delete(
        self, scheda_alunno_id: int, materiale_id: int, utente: Utente
    ) -> None:
        scheda, iscrizione = await self._scheda_e_iscrizione(scheda_alunno_id)
        assert_puo_scrivere_scheda(utente, iscrizione.corso)
        materiale = await self._materiale_di_scheda(scheda_alunno_id, materiale_id)
        if materiale.storage_key is not None:
            await storage.delete(materiale.storage_key)
        await self.repo.delete(materiale)
        self.scheda_repo.expire(scheda)
