"""Primitivi di sicurezza: hashing password, JWT, token di sessione.

Modulo puro (nessuna dipendenza dal DB) usato dai servizi di autenticazione.
Due piani distinti:

- **Service account (macchina-a-macchina)** → JWT firmati HS256, stateless.
- **Utenti umani** → token di sessione opachi, di cui il DB conserva solo
  l'hash SHA-256 (vedi :mod:`app.models.sessione`).
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings

# ── Password (bcrypt) ────────────────────────────────────────────────────────


def hash_password(password: str) -> str:
    """Genera l'hash bcrypt di una password in chiaro."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica una password in chiaro contro il suo hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Hash malformato → mai valido.
        return False


# ── JWT (service account) ────────────────────────────────────────────────────


def create_access_token(subject: str, *, expires_minutes: int | None = None) -> str:
    """Crea un JWT firmato per un service account.

    ``subject`` è l'id dell'utente (service account). Il claim ``type`` marca il
    token come piano macchina-a-macchina.
    """
    minutes = (
        expires_minutes if expires_minutes is not None else settings.jwt_expire_minutes
    )
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "service",
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(
        payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodifica e valida un JWT. Solleva ``jwt.InvalidTokenError`` se invalido."""
    return jwt.decode(
        token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
    )


# ── Token di sessione (utenti umani) ─────────────────────────────────────────


def generate_session_token() -> str:
    """Genera un token di sessione opaco, crittograficamente casuale."""
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    """Hash SHA-256 (esadecimale) di un token di sessione.

    Persistiamo solo l'hash: anche con accesso al DB il token in chiaro non è
    ricostruibile. SHA-256 è adeguato perché il token ha già alta entropia.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
