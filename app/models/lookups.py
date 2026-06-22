from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.relations import bande_indirizzi, voci_sottovoci_rendiconto

if TYPE_CHECKING:
    from app.models.indirizzo import Indirizzo


class LookupBase(Base):
    """Base astratta per le tabelle dimensione (``D_*``).

    Ogni tabella di lookup è una coppia codice/descrizione: il ``codice`` è una
    chiave primaria assegnata esplicitamente (i codici sono dati di riferimento
    stabili, non generati dal database).
    """

    __abstract__ = True

    codice: Mapped[int] = mapped_column(
        SmallInteger, primary_key=True, autoincrement=False
    )
    descrizione: Mapped[str] = mapped_column(String(100))


class Stato(LookupBase):
    __tablename__ = "stati"


class Regione(LookupBase):
    __tablename__ = "regioni"

    stato_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("stati.codice"), nullable=True
    )


class Provincia(LookupBase):
    __tablename__ = "province"

    sigla: Mapped[str | None] = mapped_column(String(5), nullable=True)
    regione_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("regioni.codice"), nullable=True
    )


class Comune(LookupBase):
    __tablename__ = "comuni"

    codice_catastale: Mapped[str | None] = mapped_column(String(6), nullable=True)
    provincia_codice: Mapped[int | None] = mapped_column(
        SmallInteger, ForeignKey("province.codice"), nullable=True
    )

    provincia: Mapped[Provincia | None] = relationship(
        "Provincia", foreign_keys=[provincia_codice]
    )


class Strumento(LookupBase):
    __tablename__ = "strumenti"


class TipoIndirizzo(LookupBase):
    __tablename__ = "tipi_indirizzo"


class Banda(LookupBase):
    __tablename__ = "bande"

    indirizzi: Mapped[list[Indirizzo]] = relationship(
        secondary=bande_indirizzi, back_populates="bande"
    )


class RuoloContatto(LookupBase):
    __tablename__ = "ruoli_contatto"


class RuoloBanda(LookupBase):
    __tablename__ = "ruoli_banda"


# ── Contabilità (Pass 2b) ────────────────────────────────────────────────────
class SezioneRendiconto(LookupBase):
    __tablename__ = "sezioni_rendiconto"


class VoceRendiconto(LookupBase):
    __tablename__ = "voci_rendiconto"

    # Legacy D_VoceRendiconto.Descrizione è VARCHAR(255).
    descrizione: Mapped[str] = mapped_column(String(255))
    # Ogni voce appartiene a una sezione (Uscite/Entrate/…). La gerarchia, nel
    # modello legacy, viveva solo implicitamente nelle voci di contabilità.
    sezione_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("sezioni_rendiconto.codice"), nullable=False
    )

    sezione: Mapped[SezioneRendiconto] = relationship(
        "SezioneRendiconto", foreign_keys=[sezione_codice]
    )
    sottovoci: Mapped[list[SottovoceRendiconto]] = relationship(
        "SottovoceRendiconto",
        secondary=voci_sottovoci_rendiconto,
        back_populates="voci",
    )


class SottovoceRendiconto(LookupBase):
    __tablename__ = "sottovoci_rendiconto"

    # Legacy D_SottovoceRendiconto.Descrizione è VARCHAR(255).
    descrizione: Mapped[str] = mapped_column(String(255))

    voci: Mapped[list[VoceRendiconto]] = relationship(
        "VoceRendiconto",
        secondary=voci_sottovoci_rendiconto,
        back_populates="sottovoci",
    )


class NaturaFlusso(LookupBase):
    __tablename__ = "nature_flusso"


# ── Archivio documentale (Pass 3) ────────────────────────────────────────────
class TipoDocumento(LookupBase):
    __tablename__ = "tipi_documento"


class TipoSpartito(LookupBase):
    __tablename__ = "tipi_spartito"


class StatoIscrizione(LookupBase):
    __tablename__ = "stati_iscrizione"
