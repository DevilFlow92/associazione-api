from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.api.deps import get_auth_service, get_current_user
from app.core.config import settings
from app.exceptions.auth import InactiveUserError, InvalidCredentialsError
from app.models.utente import Utente
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    TokenRequest,
    TokenResponse,
)
from app.schemas.utente import UtenteResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=MessageResponse)
async def login(
    data: LoginRequest,
    response: Response,
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Login umano: apre una sessione server-side e imposta il cookie."""
    try:
        token = await service.login(data.email, data.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    except InactiveUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_expire_hours * 3600,
    )
    return MessageResponse(detail="Login effettuato")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    response: Response,
    service: AuthService = Depends(get_auth_service),
    _user: Utente = Depends(get_current_user),
) -> MessageResponse:
    """Revoca la sessione corrente e cancella il cookie."""
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        await service.logout(token)
    response.delete_cookie(key=settings.session_cookie_name)
    return MessageResponse(detail="Logout effettuato")


@router.post("/token", response_model=TokenResponse)
async def issue_token(
    data: TokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Rilascia un JWT a un service account (piano macchina-a-macchina)."""
    try:
        token, expires_in = await service.issue_token(data.email, data.password)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e)
        ) from e
    except InactiveUserError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UtenteResponse)
async def read_me(user: Utente = Depends(get_current_user)) -> UtenteResponse:
    """Restituisce il profilo (e i ruoli/permessi) dell'utente autenticato."""
    return UtenteResponse.model_validate(user)
