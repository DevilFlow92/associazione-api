from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, String, Table

from app.core.database import Base

# Relazione molti-a-molti tra persone e indirizzi (legacy: T_R_Persona_Indirizzo).
# Una persona può avere più indirizzi (residenza, corrispondenza, ...) e un
# indirizzo può essere condiviso da più persone.
persone_indirizzi = Table(
    "persone_indirizzi",
    Base.metadata,
    Column("persona_id", Integer, ForeignKey("persone.id"), primary_key=True),
    Column("indirizzo_id", Integer, ForeignKey("indirizzi.id"), primary_key=True),
)

# Relazione molti-a-molti tra bande e indirizzi (legacy: T_R_Banda_Indirizzo).
# Una banda può avere più indirizzi (sede legale, sede operativa, ...).
bande_indirizzi = Table(
    "bande_indirizzi",
    Base.metadata,
    Column("banda_codice", SmallInteger, ForeignKey("bande.codice"), primary_key=True),
    Column("indirizzo_id", Integer, ForeignKey("indirizzi.id"), primary_key=True),
)

# Relazione molti-a-molti tra voci e sottovoci del rendiconto.
# Le sottovoci "generiche" di uscita (Materie prime, Servizi, Godimento beni di
# terzi, Personale, Uscite diverse) sono condivise da più voci (A/B/E Uscite):
# il legame voce↔sottovoce non è quindi una semplice FK 1:N ma una tabella
# ponte. ``ondelete="CASCADE"`` rimuove i link quando una voce o una sottovoce
# viene cancellata.
voci_sottovoci_rendiconto = Table(
    "voci_sottovoci_rendiconto",
    Base.metadata,
    Column(
        "voce_codice",
        SmallInteger,
        ForeignKey("voci_rendiconto.codice", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "sottovoce_codice",
        SmallInteger,
        ForeignKey("sottovoci_rendiconto.codice", ondelete="CASCADE"),
        primary_key=True,
    ),
)

# ── RBAC: assegnazioni molti-a-molti ─────────────────────────────────────────
# Quali permessi concede un ruolo. Il modello RBAC è configurabile per
# associazione: ogni banda decide quali permessi mappare ai ruoli del direttivo
# senza modifiche al codice.
ruoli_permessi = Table(
    "ruoli_permessi",
    Base.metadata,
    Column("ruolo_id", Integer, ForeignKey("ruoli.id"), primary_key=True),
    Column(
        "permesso_codice", String(64), ForeignKey("permessi.codice"), primary_key=True
    ),
)

# Quali ruoli ha un utente (umano o service account).
utenti_ruoli = Table(
    "utenti_ruoli",
    Base.metadata,
    Column("utente_id", Integer, ForeignKey("utenti.id"), primary_key=True),
    Column("ruolo_id", Integer, ForeignKey("ruoli.id"), primary_key=True),
)
