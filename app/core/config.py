from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    app_env: str = "development"
    app_debug: bool = True
    secret_key: str = "changeme"

    # Database
    database_url: str | None = None
    # URL usato per le migrazioni (DDL). In produzione punta al proprietario
    # dello schema, distinto dal ruolo a privilegio minimo dell'app a runtime.
    # Se non impostato, ricade su ``database_url``.
    migration_database_url: str | None = None

    # ── Autenticazione ───────────────────────────────────────────────────────
    # Chiave di firma dei JWT (service account macchina-a-macchina). In
    # produzione DEVE essere sovrascritta da variabile d'ambiente.
    jwt_secret_key: str = "changeme"
    jwt_algorithm: str = "HS256"
    # Durata del token JWT dei service account (minuti). Lunga: i service
    # account sono stateless e long-lived.
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 giorni

    # Sessioni utenti umani (server-side). Durata di validità di una sessione
    # in ore e nome del cookie che trasporta il token opaco.
    session_expire_hours: int = 12
    session_cookie_name: str = "session_token"
    # Marca il cookie come Secure (solo HTTPS). In sviluppo locale via HTTP va
    # disattivato, altrimenti il browser non lo invia.
    session_cookie_secure: bool = False

    @field_validator("database_url", "migration_database_url")
    @classmethod
    def _force_async_driver(cls, v: str | None) -> str | None:
        if v is None:
            return v
        if v.startswith("postgres://"):
            v = "postgresql://" + v[len("postgres://") :]
        if v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v


settings = Settings()
