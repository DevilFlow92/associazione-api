"""seed catalogo voci programma — categorie, flauti, voci

Popola ``categorie_voce_programma`` (tecnica, scale, repertorio, teoria),
aggiunge il tipo corso ``Flauti`` a ``tipi_corso`` e seeda
``voci_programma_catalogo`` con un programma didattico di base per ciascun
tipo di corso esistente (ottoni, percussioni, ance, pianoforte, flauti).

Revision ID: f56e876f377b
Revises: e1b400fd92b3
Create Date: 2026-08-23 00:00:00.000001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f56e876f377b"
down_revision: str | Sequence[str] | None = "e1b400fd92b3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

CATEGORIE = [
    (1, "Tecnica"),
    (2, "Scale"),
    (3, "Repertorio"),
    (4, "Teoria"),
]

TIPO_CORSO_FLAUTI = (5, "Flauti")

# (tipo_corso_codice, testo, categoria_codice, livello)
OTTONI = 1
PERCUSSIONI = 2
ANCE = 3
PIANOFORTE = 4
FLAUTI = 5

VOCI: list[tuple[int, str, int, int]] = [
    # Ottoni
    (OTTONI, "Impostazione dell'imboccatura", 1, 1),
    (OTTONI, "Respirazione diaframmatica", 1, 1),
    (OTTONI, "Buzzing con bocchino", 1, 1),
    (OTTONI, "Note lunghe", 1, 1),
    (OTTONI, "Staccato semplice", 1, 2),
    (OTTONI, "Flessibilità (legature naturali)", 1, 2),
    (OTTONI, "Estensione del registro", 1, 3),
    (OTTONI, "Scala di Si♭ maggiore", 2, 1),
    (OTTONI, "Scala di Fa maggiore", 2, 1),
    (OTTONI, "Scala di Mi♭ maggiore", 2, 2),
    (OTTONI, "Scala cromatica", 2, 2),
    (OTTONI, "Arpeggi maggiori", 2, 3),
    (OTTONI, "Studi dal metodo", 3, 1),
    (OTTONI, "Parte di banda", 3, 2),
    (OTTONI, "Duetto", 3, 2),
    (OTTONI, "Brano solistico", 3, 3),
    (OTTONI, "Lettura ritmica", 4, 1),
    (OTTONI, "Valori e pause", 4, 1),
    (OTTONI, "Chiave di violino", 4, 1),
    (OTTONI, "Alterazioni", 4, 2),
    (OTTONI, "Dinamiche", 4, 2),
    # Ance
    (ANCE, "Impostazione dell'imboccatura", 1, 1),
    (ANCE, "Controllo dell'ancia", 1, 1),
    (ANCE, "Respirazione diaframmatica", 1, 1),
    (ANCE, "Note lunghe", 1, 1),
    (ANCE, "Staccato semplice", 1, 2),
    (ANCE, "Cambio di registro", 1, 2),
    (ANCE, "Agilità digitale", 1, 3),
    (ANCE, "Scala di Do maggiore", 2, 1),
    (ANCE, "Scala di Sol maggiore", 2, 1),
    (ANCE, "Scala di Fa maggiore", 2, 2),
    (ANCE, "Scala di La minore", 2, 2),
    (ANCE, "Scala cromatica", 2, 2),
    (ANCE, "Arpeggi maggiori", 2, 3),
    (ANCE, "Studi dal metodo", 3, 1),
    (ANCE, "Studio melodico", 3, 2),
    (ANCE, "Parte di banda", 3, 2),
    (ANCE, "Duetto", 3, 2),
    (ANCE, "Brano solistico", 3, 3),
    (ANCE, "Lettura ritmica", 4, 1),
    (ANCE, "Valori e pause", 4, 1),
    (ANCE, "Chiave di violino", 4, 1),
    (ANCE, "Alterazioni", 4, 2),
    (ANCE, "Dinamiche", 4, 2),
    # Percussioni
    (PERCUSSIONI, "Impugnatura delle bacchette", 1, 1),
    (PERCUSSIONI, "Colpo singolo", 1, 1),
    (PERCUSSIONI, "Colpo doppio", 1, 1),
    (PERCUSSIONI, "Controllo delle dinamiche", 1, 2),
    (PERCUSSIONI, "Rullo", 1, 2),
    (PERCUSSIONI, "Paradiddle", 1, 2),
    (PERCUSSIONI, "Indipendenza degli arti", 1, 3),
    (PERCUSSIONI, "Scala di Do maggiore su tastiera", 2, 1),
    (PERCUSSIONI, "Scala di Sol maggiore su tastiera", 2, 2),
    (PERCUSSIONI, "Arpeggi su tastiera", 2, 3),
    (PERCUSSIONI, "Studi per tamburo", 3, 1),
    (PERCUSSIONI, "Parte di banda (rullante)", 3, 2),
    (PERCUSSIONI, "Parte di banda (grancassa e piatti)", 3, 2),
    (PERCUSSIONI, "Studio per tastiere", 3, 3),
    (PERCUSSIONI, "Lettura ritmica", 4, 1),
    (PERCUSSIONI, "Valori e pause", 4, 1),
    (PERCUSSIONI, "Rudimenti", 4, 2),
    (PERCUSSIONI, "Tempi semplici e composti", 4, 2),
    (PERCUSSIONI, "Dinamiche", 4, 2),
    # Pianoforte
    (PIANOFORTE, "Postura e posizione della mano", 1, 1),
    (PIANOFORTE, "Indipendenza delle dita", 1, 1),
    (PIANOFORTE, "Legato e staccato", 1, 1),
    (PIANOFORTE, "Passaggio del pollice", 1, 2),
    (PIANOFORTE, "Scale a mani unite", 1, 2),
    (PIANOFORTE, "Uso del pedale", 1, 3),
    (PIANOFORTE, "Scala di Do maggiore", 2, 1),
    (PIANOFORTE, "Scala di Sol maggiore", 2, 1),
    (PIANOFORTE, "Scala di Fa maggiore", 2, 2),
    (PIANOFORTE, "Scala di La minore", 2, 2),
    (PIANOFORTE, "Arpeggi", 2, 2),
    (PIANOFORTE, "Moto contrario", 2, 3),
    (PIANOFORTE, "Studi dal metodo", 3, 1),
    (PIANOFORTE, "Studio tecnico", 3, 2),
    (PIANOFORTE, "Brano del repertorio classico", 3, 2),
    (PIANOFORTE, "Brano a quattro mani", 3, 3),
    (PIANOFORTE, "Lettura ritmica", 4, 1),
    (PIANOFORTE, "Valori e pause", 4, 1),
    (PIANOFORTE, "Chiave di violino e basso", 4, 1),
    (PIANOFORTE, "Triadi e accordi", 4, 2),
    (PIANOFORTE, "Dinamiche", 4, 2),
    # Flauti
    (FLAUTI, "Impostazione dell'imboccatura", 1, 1),
    (FLAUTI, "Emissione e intonazione", 1, 1),
    (FLAUTI, "Respirazione diaframmatica", 1, 1),
    (FLAUTI, "Note lunghe", 1, 1),
    (FLAUTI, "Staccato semplice", 1, 2),
    (FLAUTI, "Cambio di registro", 1, 2),
    (FLAUTI, "Agilità digitale", 1, 2),
    (FLAUTI, "Vibrato", 1, 3),
    (FLAUTI, "Scala di Do maggiore", 2, 1),
    (FLAUTI, "Scala di Sol maggiore", 2, 1),
    (FLAUTI, "Scala di Fa maggiore", 2, 2),
    (FLAUTI, "Scala di La minore", 2, 2),
    (FLAUTI, "Scala cromatica", 2, 2),
    (FLAUTI, "Arpeggi maggiori", 2, 3),
    (FLAUTI, "Studi dal metodo", 3, 1),
    (FLAUTI, "Studio melodico", 3, 2),
    (FLAUTI, "Parte di banda", 3, 2),
    (FLAUTI, "Duetto", 3, 2),
    (FLAUTI, "Brano solistico", 3, 3),
    (FLAUTI, "Lettura ritmica", 4, 1),
    (FLAUTI, "Valori e pause", 4, 1),
    (FLAUTI, "Chiave di violino", 4, 1),
    (FLAUTI, "Alterazioni", 4, 2),
    (FLAUTI, "Dinamiche", 4, 2),
]


def upgrade() -> None:
    bind = op.get_bind()

    for codice, descrizione in CATEGORIE:
        bind.execute(
            sa.text(
                "INSERT INTO categorie_voce_programma (codice, descrizione) "
                "VALUES (:c, :d) ON CONFLICT DO NOTHING"
            ),
            {"c": codice, "d": descrizione},
        )

    bind.execute(
        sa.text(
            "INSERT INTO tipi_corso (codice, descrizione) "
            "VALUES (:c, :d) ON CONFLICT DO NOTHING"
        ),
        {"c": TIPO_CORSO_FLAUTI[0], "d": TIPO_CORSO_FLAUTI[1]},
    )

    for tipo_corso_codice, testo, categoria_codice, livello in VOCI:
        bind.execute(
            sa.text(
                "INSERT INTO voci_programma_catalogo "
                "(tipo_corso_codice, testo, categoria_codice, livello, attiva) "
                "VALUES (:t, :x, :c, :l, true) "
                "ON CONFLICT ON CONSTRAINT uq_voci_programma_catalogo_tipo_corso_testo "
                "DO NOTHING"
            ),
            {"t": tipo_corso_codice, "x": testo, "c": categoria_codice, "l": livello},
        )


def downgrade() -> None:
    bind = op.get_bind()

    for tipo_corso_codice, testo, _categoria_codice, _livello in VOCI:
        bind.execute(
            sa.text(
                "DELETE FROM voci_programma_catalogo "
                "WHERE tipo_corso_codice = :t AND testo = :x"
            ),
            {"t": tipo_corso_codice, "x": testo},
        )

    bind.execute(
        sa.text("DELETE FROM tipi_corso WHERE codice = :c"),
        {"c": TIPO_CORSO_FLAUTI[0]},
    )

    bind.execute(sa.text("DELETE FROM categorie_voce_programma"))
