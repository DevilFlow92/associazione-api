from __future__ import annotations

import io
from dataclasses import dataclass, field

from pypdf import PdfWriter

from app.core.storage import Storage, StorageFileNotFoundError
from app.exceptions.libretto import (
    PersonaNonInOrganicoError,
    PersonaNonInOrganicoProvaError,
    ProvaSenzaOrganicoError,
    ProvaSenzaRepertorioError,
    ServizioSenzaOrganicoError,
    ServizioSenzaRepertorioError,
)
from app.exceptions.prova import ProvaNotFoundError
from app.exceptions.servizio import ServizioNotFoundError
from app.models.persona import Persona
from app.models.presenza import Presenza
from app.models.repertorio_item import RepertorioItem
from app.models.spartito import Spartito
from app.repositories.presenza_repository import PresenzaRepository
from app.repositories.prova_repository import ProvaRepository
from app.repositories.repertorio_item_repository import RepertorioItemRepository
from app.repositories.servizio_repository import ServizioRepository


@dataclass
class BranoMancante:
    nome_parte_id: int
    nome_parte_nome: str
    motivo: str


@dataclass
class LibrettoPersona:
    """Esito della generazione del libretto per una singola persona.

    ``pdf_bytes`` è ``None`` quando non è stato trovato nessuno spartito per
    nessun brano del repertorio (libretto vuoto) — sta al chiamante decidere
    se trattarlo come errore (download singolo) o come voce "senza spartiti"
    in un report (download collettivo).
    """

    persona_id: int
    nome: str | None
    cognome: str | None
    pdf_bytes: bytes | None
    strumento_indeterminato: bool
    brani_mancanti: list[BranoMancante] = field(default_factory=list)


def _strumento_di(persona: Persona) -> int | None:
    """Risolve lo strumento di una persona per il libretto.

    Priorità a Esterno (``strumento_codice`` obbligatorio sul modello); se la
    persona non è un esterno si guarda il Socio, il cui strumento è invece
    facoltativo (può non essere ancora tracciato) — in quel caso lo strumento
    resta indeterminato, gestito esplicitamente dal chiamante.
    """
    for esterno in persona.esterni:
        if esterno.strumento_codice is not None:
            return esterno.strumento_codice
    for socio in persona.soci:
        if socio.strumento_codice is not None:
            return socio.strumento_codice
    return None


def _spartito_per_strumento(
    spartiti: list[Spartito], strumento_codice: int | None
) -> Spartito | None:
    """Sceglie lo spartito giusto per un brano e una persona.

    Priorità allo spartito specifico per lo strumento della persona; se non
    esiste, fallback allo spartito a ``strumento_codice`` nullo (il PDF unico
    che contiene già tutte le parti).
    """
    if strumento_codice is not None:
        for spartito in spartiti:
            if spartito.strumento_codice == strumento_codice:
                return spartito
    for spartito in spartiti:
        if spartito.strumento_codice is None:
            return spartito
    return None


class LibrettoService:
    def __init__(
        self,
        servizio_repo: ServizioRepository,
        prova_repo: ProvaRepository,
        presenza_repo: PresenzaRepository,
        repertorio_repo: RepertorioItemRepository,
        storage: Storage,
    ) -> None:
        self.servizio_repo = servizio_repo
        self.prova_repo = prova_repo
        self.presenza_repo = presenza_repo
        self.repertorio_repo = repertorio_repo
        self.storage = storage

    async def build(
        self,
        *,
        servizio_id: int | None = None,
        prova_id: int | None = None,
        persona_id: int | None = None,
    ) -> list[LibrettoPersona]:
        """Costruisce il libretto per un Servizio o una Prova (mutuamente
        esclusivi, come l'arc su Presenza/RepertorioItem che li alimenta)."""
        assert (servizio_id is None) != (prova_id is None)

        presenze, repertorio = await self._fetch_organico_e_repertorio(
            servizio_id, prova_id
        )

        if persona_id is not None:
            presenze = [p for p in presenze if p.persona_id == persona_id]
            if not presenze:
                if servizio_id is not None:
                    raise PersonaNonInOrganicoError(servizio_id, persona_id)
                assert prova_id is not None
                raise PersonaNonInOrganicoProvaError(prova_id, persona_id)

        return [await self._build_persona(p, repertorio) for p in presenze]

    async def _fetch_organico_e_repertorio(
        self, servizio_id: int | None, prova_id: int | None
    ) -> tuple[list[Presenza], list[RepertorioItem]]:
        if servizio_id is not None:
            if not await self.servizio_repo.get_by_id(servizio_id):
                raise ServizioNotFoundError(servizio_id)
            presenze = await self.presenza_repo.get_by_servizio_con_strumento(
                servizio_id
            )
            if not presenze:
                raise ServizioSenzaOrganicoError(servizio_id)
            repertorio = await self.repertorio_repo.get_by_servizio_con_spartiti(
                servizio_id
            )
            if not repertorio:
                raise ServizioSenzaRepertorioError(servizio_id)
            return presenze, repertorio

        assert prova_id is not None
        if not await self.prova_repo.get_by_id(prova_id):
            raise ProvaNotFoundError(prova_id)
        presenze = await self.presenza_repo.get_by_prova_con_strumento(prova_id)
        if not presenze:
            raise ProvaSenzaOrganicoError(prova_id)
        repertorio = await self.repertorio_repo.get_by_prova_con_spartiti(prova_id)
        if not repertorio:
            raise ProvaSenzaRepertorioError(prova_id)
        return presenze, repertorio

    async def _build_persona(
        self, presenza: Presenza, repertorio: list[RepertorioItem]
    ) -> LibrettoPersona:
        persona = presenza.persona
        strumento_codice = _strumento_di(persona)

        writer = PdfWriter()
        brani_mancanti: list[BranoMancante] = []
        pagine_incluse = 0

        for item in repertorio:
            nome_parte = item.nome_parte
            spartito = _spartito_per_strumento(nome_parte.spartiti, strumento_codice)

            content: bytes | None = None
            if spartito is not None and spartito.documento_id is not None:
                try:
                    content = await self.storage.get_bytes(spartito.documento.file_path)
                except StorageFileNotFoundError:
                    content = None

            if content is None:
                motivo = (
                    "strumento non determinato per la persona"
                    if strumento_codice is None
                    else "nessuno spartito disponibile per lo strumento della persona"
                )
                brani_mancanti.append(
                    BranoMancante(nome_parte.id, nome_parte.nome, motivo)
                )
                continue

            writer.append(io.BytesIO(content))
            pagine_incluse += 1

        pdf_bytes: bytes | None = None
        if pagine_incluse > 0:
            buffer = io.BytesIO()
            writer.write(buffer)
            pdf_bytes = buffer.getvalue()

        return LibrettoPersona(
            persona_id=persona.id,
            nome=persona.nome,
            cognome=persona.cognome,
            pdf_bytes=pdf_bytes,
            strumento_indeterminato=strumento_codice is None,
            brani_mancanti=brani_mancanti,
        )
