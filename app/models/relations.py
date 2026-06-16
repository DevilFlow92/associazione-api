from sqlalchemy import Column, ForeignKey, Integer, SmallInteger, Table

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
