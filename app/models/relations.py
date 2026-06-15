from sqlalchemy import Column, ForeignKey, Integer, Table

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
