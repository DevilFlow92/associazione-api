from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.lookups import TipoSpartito
    from app.models.spartito import Spartito


class NomeParte(Base):
    """Composizione musicale — raggruppa N parti strumentali (Spartito).

    Entità principale del nuovo modello a due livelli. Una NomeParte può
    avere zero Spartiti (archivio incompleto ma accettato: le bande piccole
    possono registrare l'esistenza di un brano prima di averne i file).
    ``url_riferimento`` è un campo libero (YouTube, Spotify, mp3, qualunque
    link) — nessuna validazione di formato.
    """

    __tablename__ = "nome_parti"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(255))
    tipo_spartito_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("tipi_spartito.codice"), nullable=False
    )
    banda_codice: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("bande.codice"), nullable=False
    )
    url_riferimento: Mapped[str | None] = mapped_column(String(500), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    tipo_spartito: Mapped[TipoSpartito] = relationship(
        "TipoSpartito", foreign_keys=[tipo_spartito_codice]
    )
    spartiti: Mapped[list[Spartito]] = relationship(
        "Spartito", back_populates="nome_parte", cascade="all, delete-orphan"
    )
