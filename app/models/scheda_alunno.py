from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.iscrizione_corso import IscrizioneCorso
    from app.models.persona import Persona
    from app.models.scheda_alunno_materiale import SchedaAlunnoMateriale
    from app.models.scheda_alunno_voce import SchedaAlunnoVoce


class SchedaAlunno(Base):
    """Scheda personale dell'alunno iscritto a un corso: raccoglie le voci di
    programma (``SchedaAlunnoVoce``) assegnate dall'insegnante, ciascuna con
    il proprio stato di avanzamento — vedi ``app.models.scheda_alunno_voce``.

    Scritta da insegnante/coordinatore (``corsi:write``), leggibile dall'alunno
    a cui si riferisce. È la prima entità del progetto con un controllo di
    autorizzazione *row-level*: non basta il permesso RBAC resource:action, va
    verificato anche CHI sta chiedendo — vedi ``app/services/rbac_row_level.py``.
    L'alunno è raggiunto risalendo ``scheda -> iscrizione_corso.persona_id``,
    confrontato con ``Utente.persona_id`` del principal autenticato.

    ``iscrizione_corso_id`` è UNIQUE: una sola scheda per iscrizione. Una
    persona re-iscritta allo stesso corso (ammesso dal dominio, vedi
    ``IscrizioneCorso``) ottiene quindi una scheda distinta per iscrizione,
    non una condivisa — il programma è relativo a quella frequenza.

    ``aggiornato_da_persona_id`` è l'audit di chi ha scritto l'ultimo
    aggiornamento: valorizzato dal service con la Persona collegata all'utente
    autenticato, mai dal payload (un audit falsificabile dal client non è un
    audit). Nullable perché un utente di gestione può non avere una Persona
    collegata (``Utente.persona_id`` è opzionale).
    """

    __tablename__ = "schede_alunno"

    id: Mapped[int] = mapped_column(primary_key=True)
    iscrizione_corso_id: Mapped[int] = mapped_column(
        ForeignKey("iscrizioni_corso.id"), nullable=False, unique=True
    )
    aggiornato_da_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    iscrizione_corso: Mapped[IscrizioneCorso] = relationship(
        "IscrizioneCorso", foreign_keys=[iscrizione_corso_id]
    )
    aggiornato_da: Mapped[Persona | None] = relationship(
        "Persona", foreign_keys=[aggiornato_da_persona_id]
    )
    voci: Mapped[list[SchedaAlunnoVoce]] = relationship(
        "SchedaAlunnoVoce",
        back_populates="scheda_alunno",
        order_by="SchedaAlunnoVoce.ordine",
    )
    # Nessun order_by esplicito: a differenza di ``voci`` non c'è un campo
    # "ordine" per i materiali (non richiesto dalla card), l'ordine è quello
    # di inserimento.
    materiali: Mapped[list[SchedaAlunnoMateriale]] = relationship(
        "SchedaAlunnoMateriale", back_populates="scheda_alunno"
    )
