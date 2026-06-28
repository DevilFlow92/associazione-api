from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_nonexistent=True,
    )  # type: ignore

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
    session_cookie_secure: bool = True
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    # Dominio del cookie di sessione. In produzione impostare a ".cosequences.com"
    # per condividere il cookie tra frontend (bandapp-web-fe.vercel.app) e backend
    # (associazione-api.cosequences.com). In sviluppo lasciare None.
    session_cookie_domain: str | None = None

    # ── Email (Resend) ───────────────────────────────────────────────────────
    # Chiave API Resend (https://resend.com). Se assente, l'invio email è
    # disabilitato e i servizi che lo usano sollevano a runtime.
    resend_api_key: str | None = None
    # Mittente delle email transazionali (dominio verificato su Resend).
    email_from: str = "noreply@cosequences.com"
    # Base URL del frontend, usata per costruire i link (es. reset password).
    frontend_url: str = "https://bandapp-web-fe.vercel.app"

    # ── OAuth2 — Google ──────────────────────────────────────────────────────
    google_client_id: str | None = None
    google_client_secret: str | None = None

    # ── OAuth2 — Apple ───────────────────────────────────────────────────────
    apple_client_id: str | None = None  # "Services ID" (com.xxx.web)
    apple_team_id: str | None = None
    apple_key_id: str | None = None
    apple_private_key: str | None = None  # PEM content, newlines as \n

    # ── OAuth2 — Facebook ────────────────────────────────────────────────────
    facebook_client_id: str | None = None
    facebook_client_secret: str | None = None

    # Base URL used to build OAuth2 redirect_uri (e.g. https://associazione-api-production.up.railway.app)
    api_base_url: str = "http://localhost:8000"

    @field_validator("database_url", "migration_database_url")
    @classmethod
    def _force_async_driver(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()  # rimuove newline e spazi
        if v.startswith("postgres://"):
            v = "postgresql+asyncpg://" + v[len("postgres://") :]
        elif v.startswith("postgresql://"):
            v = "postgresql+asyncpg://" + v[len("postgresql://") :]
        return v


settings = Settings()
