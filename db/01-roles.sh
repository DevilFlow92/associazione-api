#!/bin/bash
# ============================================================================
# Utenze database a privilegio minimo (PostgreSQL)
# ----------------------------------------------------------------------------
# Eseguito una sola volta dall'entrypoint Postgres (docker-entrypoint-initdb.d)
# al primo avvio del container, dopo la creazione di POSTGRES_DB.
#
# Separa i ruoli a livello di DB dal proprietario dello schema:
#
#   * Il superuser/owner (POSTGRES_USER, es. `associazione`) possiede lo schema
#     ed esegue le migrazioni Alembic (DDL). NON va usato dall'app a runtime.
#   * app_rw → ruolo di runtime dell'API: solo DML (SELECT/INSERT/UPDATE/DELETE).
#              Nessun DDL, nessun DROP.
#   * app_ro → ruolo di sola lettura (reporting/analytics/export worker).
#
# Le password sono lette da variabili d'ambiente, con default per lo sviluppo:
#   APP_RW_PASSWORD (default: app_rw)
#   APP_RO_PASSWORD (default: app_ro)
# In produzione fornire password robuste via env / secret manager.
# ============================================================================
set -euo pipefail

APP_RW_PASSWORD="${APP_RW_PASSWORD:-app_rw}"
APP_RO_PASSWORD="${APP_RO_PASSWORD:-app_ro}"

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_USER" \
     --dbname "$POSTGRES_DB" \
     --set rw_password="$APP_RW_PASSWORD" \
     --set ro_password="$APP_RO_PASSWORD" \
     --set dbname="$POSTGRES_DB" <<'SQL'
-- Ruoli LOGIN (idempotenti). La sostituzione delle variabili psql (:'...') non
-- avviene dentro i blocchi DO $$ dollar-quoted, perciò costruiamo le CREATE
-- ROLE come stringhe e le eseguiamo con \gexec solo se il ruolo non esiste.
SELECT format('CREATE ROLE app_rw LOGIN PASSWORD %L', :'rw_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_rw')
\gexec
SELECT format('CREATE ROLE app_ro LOGIN PASSWORD %L', :'ro_password')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_ro')
\gexec

-- Connessione e uso schema.
GRANT CONNECT ON DATABASE :"dbname" TO app_rw, app_ro;
GRANT USAGE ON SCHEMA public TO app_rw, app_ro;

-- app_rw: DML completo sulle tabelle/sequenze esistenti.
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_rw;

-- app_ro: sola lettura.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_ro;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO app_ro;

-- Privilegi di default: si applicano anche agli oggetti creati in futuro dal
-- proprietario dello schema (ogni migrazione Alembic).
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO app_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO app_ro;
SQL

echo "Ruoli DB a privilegio minimo (app_rw, app_ro) creati."
