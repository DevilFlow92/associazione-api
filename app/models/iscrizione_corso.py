from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.corso import Corso
    from app.models.documento import Documento
    from app.models.lookups import StatoIscrizioneCorso
    from app.models.persona import Persona


class IscrizioneCorso(Base):
    """Iscrizione di una Persona (l'alunno) a un Corso musicale.

    Distinta da ``Iscrizione`` (adesione annuale di un Socio alla banda,
    tabella ``iscrizioni``): qui l'iscritto è una Persona qualunque, non
    necessariamente un Socio (un neofita può iscriversi a un corso senza
    ancora essere socio). ``persona_id`` referenzia ``persone.id``, stessa
    generalizzazione già adottata da ``Corso.coordinatore_persona_id`` e
    ``Ricevuta.persona_id``.

    Nessun vincolo di unicità su (persona_id, corso_id): una persona può
    essere re-iscritta allo stesso corso dopo un'iscrizione annullata.
    """

    __tablename__ = "iscrizioni_corso"

    id: Mapped[int] = mapped_column(primary_key=True)
    corso_id: Mapped[int] = mapped_column(ForeignKey("corsi.id"), nullable=False)
    persona_id: Mapped[int] = mapped_column(ForeignKey("persone.id"), nullable=False)
    stato_iscrizione_corso_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("stati_iscrizione_corso.codice"), nullable=False
    )
    documento_id: Mapped[int | None] = mapped_column(
        ForeignKey("documenti.id"), nullable=True
    )
    data_iscrizione: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    corso: Mapped[Corso] = relationship("Corso", foreign_keys=[corso_id])
    persona: Mapped[Persona] = relationship("Persona", foreign_keys=[persona_id])
    stato_iscrizione_corso: Mapped[StatoIscrizioneCorso] = relationship(
        "StatoIscrizioneCorso", foreign_keys=[stato_iscrizione_corso_codice]
    )
    documento: Mapped[Documento | None] = relationship(
        "Documento", foreign_keys=[documento_id]
    )
