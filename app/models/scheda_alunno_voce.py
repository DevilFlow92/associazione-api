from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.scheda_alunno import SchedaAlunno
    from app.models.voce_programma_catalogo import VoceProgrammaCatalogo


class StatoVoceProgramma(enum.StrEnum):
    """Stato di avanzamento di una voce di programma sulla scheda alunno."""

    DA_INIZIARE = "da_iniziare"
    IN_CORSO = "in_corso"
    ACQUISITA = "acquisita"


class SchedaAlunnoVoce(Base):
    """Voce di programma assegnata a una scheda alunno, pescata dal catalogo
    riutilizzabile (``VoceProgrammaCatalogo``) e specializzata con stato,
    dettaglio libero e ordine didattico.

    Nessun vincolo UNIQUE su (scheda_alunno_id, voce_catalogo_id): la stessa
    voce di catalogo può comparire più volte sulla stessa scheda con
    ``dettaglio`` diverso (es. "Studio n.9, battute 1-16" e "Studio n.9,
    battute 17-32" come due voci distinte).

    ``ordine`` è la sequenza didattica scelta dall'insegnante — non
    alfabetica né quella di inserimento — per questo è un intero esplicito
    e non desumibile da altri campi.

    Ogni creazione e ogni cambio di ``stato`` viene registrato in
    ``SchedaAlunnoVoceStorico`` (scritto dal service, mai da questo model).
    """

    __tablename__ = "scheda_alunno_voci"

    id: Mapped[int] = mapped_column(primary_key=True)
    scheda_alunno_id: Mapped[int] = mapped_column(
        ForeignKey("schede_alunno.id"), nullable=False
    )
    voce_catalogo_id: Mapped[int] = mapped_column(
        ForeignKey("voci_programma_catalogo.id"), nullable=False
    )
    stato: Mapped[StatoVoceProgramma] = mapped_column(
        Enum(StatoVoceProgramma, name="stato_voce_programma"), nullable=False
    )
    dettaglio: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ordine: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    scheda_alunno: Mapped[SchedaAlunno] = relationship(
        "SchedaAlunno", foreign_keys=[scheda_alunno_id], back_populates="voci"
    )
    voce_catalogo: Mapped[VoceProgrammaCatalogo] = relationship(
        "VoceProgrammaCatalogo", foreign_keys=[voce_catalogo_id]
    )
