from __future__ import annotations

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


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


class Strumento(LookupBase):
    __tablename__ = "strumenti"


class TipoIndirizzo(LookupBase):
    __tablename__ = "tipi_indirizzo"


class Banda(LookupBase):
    __tablename__ = "bande"


class RuoloContatto(LookupBase):
    __tablename__ = "ruoli_contatto"


class RuoloBanda(LookupBase):
    __tablename__ = "ruoli_banda"
