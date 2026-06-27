from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Credenziali per il login umano (sessione server-side)."""

    email: EmailStr
    password: str


class TokenRequest(BaseModel):
    """Credenziali per il rilascio di un JWT a un service account."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT rilasciato a un service account."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # secondi


class MessageResponse(BaseModel):
    detail: str


class PasswordResetRequest(BaseModel):
    """Richiesta di reset password (indirizzo email)."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Conferma del reset: token ricevuto via email + nuova password."""

    token: str
    new_password: str = Field(min_length=8)


class RegisterRequest(BaseModel):
    """Auto-registrazione di un nuovo utente con ruolo Ospite."""

    email: EmailStr
    password: str = Field(min_length=8)
    nome_completo: str | None = None
    banda_codice: int
