"""
Script di seed per il database di produzione.
Eseguire dalla Console di Railway:
    python scripts/seed_production.py

Richiede che i file SQL siano presenti in scripts/:
    - see_pass1_lookups_pg.sql  (stati, regioni, province, comuni)
"""

import os
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

SCRIPTS_DIR = Path(__file__).parent


def get_connection():
    url = os.environ.get("DATABASE_URL")
    if not url:
        print("ERROR: DATABASE_URL non impostata", file=sys.stderr)
        sys.exit(1)
    url = url.strip().replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(url)


def run_sql_file(cur, filename):
    path = SCRIPTS_DIR / filename
    if not path.exists():
        print(f"  ✗ File non trovato: {path}", file=sys.stderr)
        sys.exit(1)
    sql = path.read_text(encoding="utf-8")
    # Aggiungi UPSERT per idempotenza
    statements = [
        s.strip() for s in sql.split(";") if s.strip() and "INSERT" in s.upper()
    ]
    for stmt in statements:
        # Determina la tabella
        table = stmt.split("INTO")[1].split("(")[0].strip() if "INTO" in stmt else "?"
        print(f"    → {table}...")
        # Converti INSERT in UPSERT se non lo è già
        if "ON CONFLICT" not in stmt.upper():
            if "stati " in stmt:
                stmt += " ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione"  # noqa: E501
            elif "regioni " in stmt:
                stmt += (
                    " ON CONFLICT (codice) DO UPDATE SET "
                    "descrizione = EXCLUDED.descrizione, "
                    "stato_codice = EXCLUDED.stato_codice"
                )
            elif "province " in stmt:
                stmt += " ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione, regione_codice = EXCLUDED.regione_codice, sigla = EXCLUDED.sigla"  # noqa: E501
            elif "comuni " in stmt:
                stmt += " ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione, provincia_codice = EXCLUDED.provincia_codice, codice_catastale = EXCLUDED.codice_catastale"  # noqa: E501
        cur.execute(stmt)


def seed_lookups_pass1(cur):
    print("  → bande...")
    cur.execute("""
        INSERT INTO bande (codice, descrizione) VALUES
            (1, 'Associazione Musicale "S. Antonio" Banda Musicale Città di Quartu')
        ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione
    """)

    print("  → ruoli_banda...")
    execute_values(
        cur,
        "INSERT INTO ruoli_banda (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Presidente"),
            (2, "Vice Presidente"),
            (3, "Tesoriere"),
            (4, "Segretario"),
            (5, "Consigliere"),
            (6, "Direttore Artistico"),
            (7, "Maestro Corsi di Strumento"),
            (8, "Maestro della Banda"),
            (9, "Supporter Associazione"),
            (10, "Socio Bandista"),
            (11, "Socio Allievo"),
        ],
    )

    print("  → ruoli_contatto...")
    execute_values(
        cur,
        "INSERT INTO ruoli_contatto (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [(1, "Contatto Principale"), (2, "Contatto Alternativo")],
    )

    print("  → strumenti...")
    execute_values(
        cur,
        "INSERT INTO strumenti (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Flauto"),
            (2, "Ottavino"),
            (3, "Piccolo Mib"),
            (4, "Clarinetto"),
            (5, "Tromba"),
            (6, "Sax Soprano"),
            (7, "Sax Contralto"),
            (8, "Sax Tenore"),
            (9, "Sax Baritono"),
            (10, "Trombone"),
            (11, "Flicorno Soprano"),
            (12, "Flicorno Contralto"),
            (13, "Flicorno Tenore"),
            (14, "Euphonium"),
            (15, "Corno"),
            (16, "Tuba"),
            (17, "Percussioni"),
            (18, "Direttore Artistico"),
            (19, "Insegnante"),
            (20, "Clarinetto/Sax"),
            (21, "Cantante"),
            (22, "Tastiera"),
            (23, "Chitarra"),
            (24, "Basso Elettrico"),
            (25, "Oboe"),
            (26, "Service"),
            (27, "Ballerino/a"),
            (28, "Da verificare"),
        ],
    )

    print("  → tipi_indirizzo...")
    execute_values(
        cur,
        "INSERT INTO tipi_indirizzo (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Sede Legale"),
            (2, "Residenza"),
            (3, "Corrispondenza"),
            (4, "Servizio"),
            (5, "Sede Operativa"),
        ],
    )

    print("  → indirizzi...")
    cur.execute("""
        INSERT INTO indirizzi (tipo_indirizzo_codice, prima_riga, seconda_riga, cap, comune_codice)
        SELECT 1, 'Via Merello 126 Piano 1', 'C/O Studio Rundeddu', '09045', NULL
        WHERE NOT EXISTS (
            SELECT 1 FROM indirizzi WHERE prima_riga = 'Via Merello 126 Piano 1'
        )
    """)  # noqa: E501


def seed_contabilita(cur):
    print("  → nature_flusso...")
    execute_values(
        cur,
        "INSERT INTO nature_flusso (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [(1, "Cassa"), (2, "Banca")],
    )

    print("  → sezioni_rendiconto...")
    execute_values(
        cur,
        "INSERT INTO sezioni_rendiconto (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Uscite"),
            (2, "Entrate"),
            (3, "Fuori Bilancio"),
            (4, "Costi e proventi figurativi"),
        ],
    )

    print("  → voci_rendiconto...")
    execute_values(
        cur,
        "INSERT INTO voci_rendiconto (codice, descrizione, sezione_codice) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione, sezione_codice = EXCLUDED.sezione_codice",  # noqa: E501
        [
            (1, "A) Uscite da attività di interesse generale", 1),
            (2, "A) Entrate da attività di interesse generale", 2),
            (3, "B) Uscite da attività diverse", 1),
            (4, "B) Entrate da attività diverse", 2),
            (5, "C) Uscite da attività di raccolta fondi", 1),
            (6, "C) Entrate da attività di raccolta fondi", 2),
            (8, "D) Uscite da attività finanziarie e patrimoniali", 1),
            (9, "D) Entrate da attività finanziarie e patrimoniali", 2),
            (10, "E) Uscite di supporto generale", 1),
            (11, "E) Entrate di supporto generale", 2),
            (
                12,
                "Uscite da investimenti in immobilizzazioni o da deflussi di capitale di terzi",  # noqa: E501
                1,
            ),
            (
                13,
                "Entrate da disinvestimenti in immobilizzazioni o da flussi di capitale di terzi",  # noqa: E501
                2,
            ),
            (14, "Fuori Bilancio", 3),
            (15, "Costi e proventi figurativi", 4),
        ],
    )

    print("  → sottovoci_rendiconto...")
    execute_values(
        cur,
        "INSERT INTO sottovoci_rendiconto (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "1) Materie prime, sussidiarie, di consumo e di merci"),
            (2, "2) Servizi"),
            (3, "3) Godimento beni di terzi"),
            (4, "4) Personale"),
            (5, "5) Uscite diverse di gestione"),
            (6, "1) Entrate da quote associative e apporti dei fondatori"),
            (7, "2) Entrate dagli associati per attività mutuali"),
            (8, "3) Entrate per prestazioni e cessioni ad associati e fondatori"),
            (9, "4) Erogazioni liberali"),
            (10, "5) Entrate del 5 per mille"),
            (11, "6) Contributi da soggetti privati"),
            (12, "7) Entrate per prestazioni e cessioni a terzi"),
            (13, "8) Contributi da enti pubblici"),
            (14, "9) Entrate da contratti con enti pubblici"),
            (15, "10) Altre entrate"),
            (16, "1) Entrate per prestazioni e cessioni ad associati e fondatori"),
            (17, "2) Contributi da soggetti privati"),
            (18, "3) Entrate per prestazioni e cessioni a terzi"),
            (19, "4) Contributi da enti pubblici"),
            (20, "5) Entrate da contratti con enti pubblici"),
            (21, "6) Altre entrate"),
            (22, "1) Uscite per raccolte fondi abituali"),
            (23, "2) Uscite per raccolte fondi occasionali"),
            (24, "3) Altre uscite"),
            (25, "1) Entrate da raccolte fondi abituali"),
            (26, "2) Entrate da raccolte fondi occasionali"),
            (27, "3) Altre entrate"),
            (28, "1) Su rapporti bancari"),
            (29, "2) Su investimenti finanziari"),
            (30, "3) Su patrimonio edilizio"),
            (31, "4) Su altri beni patrimoniali"),
            (32, "5) Altre uscite"),
            (33, "1) Da rapporti bancari"),
            (34, "2) Da altri investimenti finanziari"),
            (35, "3) Da patrimonio edilizio"),
            (36, "4) Da altri beni patrimoniali"),
            (37, "5) Altre entrate"),
            (38, "1) Entrate da distacco del personale"),
            (39, "2) Altre entrate di supporto generale"),
            (
                40,
                "1) Investimenti in immobilizzazioni inerenti alle attività di interesse generale",  # noqa: E501
            ),
            (41, "2) Investimenti in immobilizzazioni inerenti alle attività diverse"),
            (42, "3) Investimenti in attività finanziarie e patrimoniali"),
            (43, "4) Rimborso di finanziamenti per quota capitale e di prestiti"),
            (
                44,
                "1) Disinvestimenti di immobilizzazioni inerenti alle attività di interesse generale",  # noqa: E501
            ),
            (
                45,
                "2) Disinvestimenti di immobilizzazioni inerenti alle attività diverse",
            ),
            (46, "3) Disinvestimenti di attività finanziarie e patrimoniali"),
            (47, "4) Ricevimento di finanziamenti e di prestiti"),
            (48, "1) da attività di interesse generale"),
            (49, "2) da attività diverse"),
            (50, "Fuori Bilancio"),
        ],
    )

    print("  → voci_sottovoci_rendiconto...")
    execute_values(
        cur,
        "INSERT INTO voci_sottovoci_rendiconto (voce_codice, sottovoce_codice) VALUES %s "  # noqa: E501
        "ON CONFLICT (voce_codice, sottovoce_codice) DO NOTHING",
        [
            (1, 1),
            (1, 2),
            (1, 3),
            (1, 4),
            (1, 5),
            (2, 6),
            (2, 7),
            (2, 8),
            (2, 9),
            (2, 10),
            (2, 11),
            (2, 12),
            (2, 13),
            (2, 14),
            (2, 15),
            (3, 1),
            (3, 2),
            (3, 3),
            (3, 4),
            (3, 5),
            (4, 16),
            (4, 17),
            (4, 18),
            (4, 19),
            (4, 20),
            (4, 21),
            (5, 22),
            (5, 23),
            (5, 24),
            (6, 25),
            (6, 26),
            (6, 27),
            (8, 28),
            (8, 29),
            (8, 30),
            (8, 31),
            (8, 32),
            (9, 33),
            (9, 34),
            (9, 35),
            (9, 36),
            (9, 37),
            (10, 1),
            (10, 2),
            (10, 3),
            (10, 4),
            (10, 5),
            (11, 38),
            (11, 39),
            (12, 40),
            (12, 41),
            (12, 42),
            (12, 43),
            (13, 44),
            (13, 45),
            (13, 46),
            (13, 47),
            (14, 50),
            (15, 48),
            (15, 49),
        ],
    )


def seed_pass3(cur):
    print("  → tipi_documento...")
    execute_values(
        cur,
        "INSERT INTO tipi_documento (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Modulo iscrizione"),
            (2, "Ricevuta"),
            (3, "Spartito"),
            (4, "Comunicazione"),
            (5, "Rendiconto"),
            (6, "Altro"),
        ],
    )

    print("  → tipi_spartito...")
    execute_values(
        cur,
        "INSERT INTO tipi_spartito (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [
            (1, "Marcia festiva"),
            (2, "Inno religioso"),
            (3, "Marcia funebre"),
            (4, "Brano da concerto"),
        ],
    )

    print("  → stati_iscrizione...")
    execute_values(
        cur,
        "INSERT INTO stati_iscrizione (codice, descrizione) VALUES %s "
        "ON CONFLICT (codice) DO UPDATE SET descrizione = EXCLUDED.descrizione",
        [(1, "Da pagare"), (2, "Pagata"), (3, "Annullata")],
    )


def seed_service_accounts(cur):
    print("  → utenti (service accounts)...")
    cur.execute("""
        INSERT INTO utenti (tipo, email, password_hash, nome_completo, attivo, superuser, creato_il, aggiornato_il)
        VALUES (
            'SERVIZIO',
            'sa-associazione-api@cosequences.com',
            '$2b$12$fXgvlKhT5EC.VJ6YGzJOZeMZZon2zJJRqqB.UvVUhNBV2Y6SbnV2u',
            'sa-associazione-api',
            true,
            false,
            now(),
            now()
        )
        ON CONFLICT (email) DO NOTHING
    """)  # noqa: E501


def main():
    print("Connessione al database...")
    conn = get_connection()
    cur = conn.cursor()

    try:
        print("\n[Pass 1] Lookup geografici (stati/regioni/province/comuni)...")
        run_sql_file(cur, "see_pass1_lookups_pg.sql")

        print("\n[Pass 1] Lookup applicativi...")
        seed_lookups_pass1(cur)

        print("\n[Pass 2] Contabilità...")
        seed_contabilita(cur)

        print("\n[Pass 3] Tipi documento / spartito / stati iscrizione...")
        seed_pass3(cur)

        print("\n[Service accounts]...")
        seed_service_accounts(cur)

        conn.commit()
        print("\n✓ Seed completato con successo.")

    except Exception as e:
        conn.rollback()
        print(f"\n✗ Errore: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
