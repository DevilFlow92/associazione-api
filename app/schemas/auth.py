from __future__ import annotations

from pydantic import BaseModel, EmailStr


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
