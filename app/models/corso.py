from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lookups import TipoCorso
    from app.models.persona import Persona


class Corso(Base):
    """Corso musicale della banda per un dato anno (es. ottoni, percussioni).

    ``coordinatore_persona_id`` e ``insegnante_persona_id`` referenziano
    ``persone.id`` (non ``soci.id``), coerente con la generalizzazione già
    adottata da ``Ricevuta.persona_id``: un insegnante può essere un esterno
    pagato, non necessariamente un socio. Entrambi nullable: un corso può
    essere aperto senza coordinatore/insegnante ancora assegnato.

    Nessun vincolo di unicità su (tipo_corso_codice, anno, banda_codice):
    corsi paralleli dello stesso tipo nello stesso anno (es. livelli diversi,
    insegnanti diversi) sono ammessi nel dominio, non un'anomalia da bloccare.
    """

    __tablename__ = "corsi"

    id: Mapped[int] = mapped_column(primary_key=True)
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    tipo_corso_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("tipi_corso.codice"), nullable=False
    )
    anno: Mapped[int] = mapped_column(Integer, nullable=False)
    coordinatore_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    insegnante_persona_id: Mapped[int | None] = mapped_column(
        ForeignKey("persone.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)

    tipo_corso: Mapped[TipoCorso] = relationship(
        "TipoCorso", foreign_keys=[tipo_corso_codice]
    )
    coordinatore: Mapped[Persona | None] = relationship(
        "Persona", foreign_keys=[coordinatore_persona_id]
    )
    insegnante: Mapped[Persona | None] = relationship(
        "Persona", foreign_keys=[insegnante_persona_id]
    )
