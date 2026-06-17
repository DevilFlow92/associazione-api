from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Permesso(Base):
    """Permesso atomico assegnabile a un ruolo.

    Dato di riferimento, chiave naturale stringa nella forma ``risorsa:azione``
    (es. ``contabilita:read``, ``utenti:write``). I permessi sono fissi nel
    codice (li dichiara l'applicazione), mentre la loro mappatura ai ruoli è
    configurabile per associazione.
    """

    __tablename__ = "permessi"

    codice: Mapped[str] = mapped_column(String(64), primary_key=True)
    descrizione: Mapped[str] = mapped_column(String(255))
