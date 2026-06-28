from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_auth_service, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.exceptions.auth import InactiveUserError, InvalidCredentialsError
from app.exceptions.utente import UtenteDuplicateEmailError
from app.models.utente import Utente
from app.repositories.password_reset_repository import PasswordResetRepository
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    PasswordResetConfirm,
    PasswordResetRequest,
    RegisterRequest,
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
        samesite=settings.session_cookie_samesite,
        domain=settings.session_cookie_domain,
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
    response.delete_cookie(
        key=settings.session_cookie_name,
        domain=settings.session_cookie_domain,
    )
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


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(
    data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Richiede un'email di reset password.

    Risponde sempre 200 per non rivelare se l'indirizzo è registrato.
    """
    reset_repo = PasswordResetRepository(db)
    await service.request_password_reset(data.email, reset_repo)
    return MessageResponse(
        detail="Se l'indirizzo è registrato, riceverai un'email con le istruzioni."
    )


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Consuma un token di reset e imposta la nuova password."""
    reset_repo = PasswordResetRepository(db)
    ok = await service.confirm_password_reset(data.token, data.new_password, reset_repo)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token non valido o scaduto.",
        )
    return MessageResponse(detail="Password aggiornata con successo.")


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> MessageResponse:
    """Auto-registrazione con ruolo Ospite."""
    try:
        await service.register(
            email=data.email,
            password=data.password,
            nome_completo=data.nome_completo,
            banda_codice=data.banda_codice,
            db=db,
        )
    except UtenteDuplicateEmailError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Esiste già un account con questa email.",
        ) from e
    return MessageResponse(
        detail="Registrazione completata. Puoi ora effettuare il login."
    )
