"""Round-trip della migrazione a7d2f1c93b08 (rendiconto: voce→sezione e
voce↔sottovoce).

Gira contro un database PostgreSQL isolato (`associazione_migtest`), creato e
distrutto dal test, così da non toccare il DB di sviluppo. Viene saltato se
PostgreSQL non è raggiungibile (es. CI senza servizio db).
"""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config

from app.core.config import settings

_REVISION = "a7d2f1c93b08"
_DOWN_REVISION = "5b0fd2895d05"

_HOST = "localhost:5432"
_CREDS = "associazione:associazione"
_ADMIN_URL = f"postgresql+psycopg2://{_CREDS}@{_HOST}/associazione_db"
_MIGTEST_DB = "associazione_migtest"
_MIGTEST_SYNC_URL = f"postgresql+psycopg2://{_CREDS}@{_HOST}/{_MIGTEST_DB}"
_MIGTEST_ASYNC_URL = f"postgresql+asyncpg://{_CREDS}@{_HOST}/{_MIGTEST_DB}"

_PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _postgres_reachable() -> bool:
    try:
        engine = sa.create_engine(_ADMIN_URL, connect_args={"connect_timeout": 2})
        with engine.connect():
            pass
        engine.dispose()
        return True
    except Exception:
        return False


def _admin_exec(statement: str) -> None:
    engine = sa.create_engine(_ADMIN_URL)
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            conn.execute(sa.text(statement))
    finally:
        engine.dispose()


def _seed_pre_migration(engine: sa.Engine) -> None:
    """Stato pre-migrazione: voci senza sezione_codice, voce 7 presente,
    nessuna sezione 4, nessuna tabella ponte."""
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                "INSERT INTO sezioni_rendiconto (codice, descrizione) VALUES "
                "(1, 'Uscite'), (2, 'Entrate'), (3, 'Fuori Bilancio')"
            )
        )
        voci = ", ".join(f"({c}, 'voce {c}')" for c in range(1, 15))
        conn.execute(
            sa.text(f"INSERT INTO voci_rendiconto (codice, descrizione) VALUES {voci}")
        )
        sottovoci = ", ".join(f"({c}, 'sottovoce {c}')" for c in range(1, 51))
        conn.execute(
            sa.text(
                "INSERT INTO sottovoci_rendiconto (codice, descrizione) VALUES "
                f"{sottovoci}"
            )
        )


def _snapshot(engine: sa.Engine) -> dict:
    insp = sa.inspect(engine)
    voci_cols = {c["name"] for c in insp.get_columns("voci_rendiconto")}
    has_junction = insp.has_table("voci_sottovoci_rendiconto")
    with engine.connect() as conn:
        voci = set(
            conn.execute(sa.text("SELECT codice FROM voci_rendiconto")).scalars()
        )
        sezioni = set(
            conn.execute(sa.text("SELECT codice FROM sezioni_rendiconto")).scalars()
        )
        junction = (
            conn.execute(
                sa.text("SELECT count(*) FROM voci_sottovoci_rendiconto")
            ).scalar_one()
            if has_junction
            else 0
        )
    return {
        "voci": voci,
        "sezioni": sezioni,
        "has_sezione_codice": "sezione_codice" in voci_cols,
        "has_junction": has_junction,
        "junction_count": junction,
    }


def _alembic_config() -> Config:
    return Config(str(_PROJECT_ROOT / "alembic.ini"))


@pytest.mark.skipif(not _postgres_reachable(), reason="PostgreSQL non raggiungibile")
def test_migration_round_trip(monkeypatch: pytest.MonkeyPatch) -> None:
    # env.py legge settings.migration_database_url a runtime: puntiamo al DB
    # isolato.
    monkeypatch.setattr(settings, "migration_database_url", _MIGTEST_ASYNC_URL)

    _admin_exec(f"DROP DATABASE IF EXISTS {_MIGTEST_DB} WITH (FORCE)")
    _admin_exec(f"CREATE DATABASE {_MIGTEST_DB}")

    cfg = _alembic_config()
    engine = sa.create_engine(_MIGTEST_SYNC_URL)
    try:
        # Schema pre-migrazione + dati di riferimento legacy.
        command.upgrade(cfg, _DOWN_REVISION)
        _seed_pre_migration(engine)
        pre = _snapshot(engine)
        assert pre["voci"] == set(range(1, 15))  # voce 7 presente
        assert pre["sezioni"] == {1, 2, 3}
        assert not pre["has_sezione_codice"]
        assert not pre["has_junction"]

        # upgrade → stato finale.
        command.upgrade(cfg, _REVISION)
        after_up = _snapshot(engine)
        assert 7 not in after_up["voci"]  # voce 7 deduplicata
        assert 15 in after_up["voci"]  # nuova voce "Costi e proventi figurativi"
        assert after_up["sezioni"] == {1, 2, 3, 4}
        assert after_up["has_sezione_codice"]
        assert after_up["junction_count"] == 60

        # downgrade → torna allo stato pre-migrazione.
        command.downgrade(cfg, _DOWN_REVISION)
        after_down = _snapshot(engine)
        assert after_down == pre

        # re-upgrade → idempotente: identico al primo upgrade.
        command.upgrade(cfg, _REVISION)
        after_up2 = _snapshot(engine)
        assert after_up2 == after_up
    finally:
        engine.dispose()
        _admin_exec(f"DROP DATABASE IF EXISTS {_MIGTEST_DB} WITH (FORCE)")
