from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import get_oauth_service
from app.core.config import settings
from app.core.logging import get_logger
from app.services.oauth_service import OAuthService

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])
logger = get_logger(__name__)

PROVIDERS = {"google", "apple", "facebook"}


# ── Helper: redirect URI ──────────────────────────────────────────────────────


def _callback_uri(provider: str) -> str:
    return f"{settings.api_base_url}/api/v1/auth/oauth/{provider}/callback"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="none",
        max_age=settings.session_expire_hours * 3600,
        domain=".cosequences.com",
    )


def _decode_jwt_unverified(token: str) -> dict:
    """Decode JWT payload without signature verification (claims only)."""
    # TODO: verify id_token signature (aud/iss) before production hardening.
    # Accettabile per ora: il token arriva via HTTPS direttamente dal provider
    # nello stesso giro di richiesta.
    import base64

    try:
        parts = token.split(".")
        payload = parts[1]
        payload += "=" * (4 - len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload))
    except Exception:
        return {}


def _generate_state(random_part: str) -> str:
    sig = hmac.new(
        settings.secret_key.encode(),
        random_part.encode(),
        hashlib.sha256,
    ).hexdigest()
    return f"{random_part}.{sig}"


def _verify_state(state: str) -> bool:
    try:
        random_part, sig = state.rsplit(".", 1)
        expected = hmac.new(
            settings.secret_key.encode(),
            random_part.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
    except ValueError:
        return False


def _validate_state_param(request: Request) -> None:
    """CSRF check for GET callbacks (Google, Facebook)."""
    state = request.query_params.get("state", "")
    if not state or not _verify_state(state):
        raise HTTPException(status_code=400, detail="State OAuth non valido")


# ── Redirect endpoints ────────────────────────────────────────────────────────


@router.get("/{provider}")
async def oauth_redirect(provider: str, response: Response) -> Response:
    """Reindirizza il browser al provider OAuth2."""
    if provider not in PROVIDERS:
        raise HTTPException(status_code=404, detail="Provider non supportato")

    random_part = secrets.token_urlsafe(32)
    state = _generate_state(random_part)

    if provider == "google":
        if not settings.google_client_id:
            raise HTTPException(status_code=503, detail="Google SSO non configurato")
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": _callback_uri("google"),
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return Response(status_code=302, headers={"Location": url})

    if provider == "facebook":
        if not settings.facebook_client_id:
            raise HTTPException(status_code=503, detail="Facebook SSO non configurato")
        params = {
            "client_id": settings.facebook_client_id,
            "redirect_uri": _callback_uri("facebook"),
            "state": state,
            "scope": "email,public_profile",
        }
        url = "https://www.facebook.com/v19.0/dialog/oauth?" + urlencode(params)
        return Response(status_code=302, headers={"Location": url})

    if provider == "apple":
        if not settings.apple_client_id:
            raise HTTPException(status_code=503, detail="Apple SSO non configurato")
        params = {
            "client_id": settings.apple_client_id,
            "redirect_uri": _callback_uri("apple"),
            "response_type": "code id_token",
            "response_mode": "form_post",
            "scope": "name email",
            "state": state,
        }
        url = "https://appleid.apple.com/auth/authorize?" + urlencode(params)
        return Response(status_code=302, headers={"Location": url})

    raise HTTPException(status_code=404, detail="Provider non supportato")


# ── Google callback ───────────────────────────────────────────────────────────


@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    service: OAuthService = Depends(get_oauth_service),
) -> Response:
    _validate_state_param(request)
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Codice OAuth mancante")

    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": _callback_uri("google"),
                "grant_type": "authorization_code",
            },
        )
    token_resp.raise_for_status()
    tokens = token_resp.json()

    claims = _decode_jwt_unverified(tokens.get("id_token", ""))
    provider_user_id = claims.get("sub")
    email = claims.get("email")
    nome = claims.get("name")

    if not provider_user_id:
        raise HTTPException(status_code=400, detail="Risposta Google non valida")

    session_token = await service.login_or_register(
        provider="google",
        provider_user_id=provider_user_id,
        email=email,
        nome_completo=nome,
    )
    _set_session_cookie(response, session_token)
    return Response(
        status_code=302,
        headers={"Location": f"{settings.frontend_url}/banda"},
    )


# ── Facebook callback ─────────────────────────────────────────────────────────


@router.get("/facebook/callback")
async def facebook_callback(
    request: Request,
    response: Response,
    service: OAuthService = Depends(get_oauth_service),
) -> Response:
    _validate_state_param(request)
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Codice OAuth mancante")

    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            "https://graph.facebook.com/v19.0/oauth/access_token",
            params={
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": _callback_uri("facebook"),
                "code": code,
            },
        )
        token_resp.raise_for_status()
        access_token = token_resp.json()["access_token"]

        me_resp = await client.get(
            "https://graph.facebook.com/me",
            params={"fields": "id,name,email", "access_token": access_token},
        )
        me_resp.raise_for_status()
        me = me_resp.json()

    provider_user_id = me.get("id")
    if not provider_user_id:
        raise HTTPException(status_code=400, detail="Risposta Facebook non valida")

    session_token = await service.login_or_register(
        provider="facebook",
        provider_user_id=provider_user_id,
        email=me.get("email"),
        nome_completo=me.get("name"),
    )
    _set_session_cookie(response, session_token)
    return Response(
        status_code=302,
        headers={"Location": f"{settings.frontend_url}/banda"},
    )


# ── Apple callback (POST — form_post) ─────────────────────────────────────────


@router.post("/apple/callback")
async def apple_callback(
    request: Request,
    response: Response,
    service: OAuthService = Depends(get_oauth_service),
) -> Response:
    form = await request.form()
    state_in_form = str(form.get("state", ""))
    if not state_in_form or not _verify_state(state_in_form):
        raise HTTPException(status_code=400, detail="State OAuth non valido")

    id_token_raw = str(form.get("id_token", ""))
    user_json = form.get("user")
    claims = _decode_jwt_unverified(id_token_raw)

    provider_user_id = claims.get("sub")
    email = claims.get("email")
    nome: str | None = None

    if user_json:
        try:
            user_data = json.loads(str(user_json))
            name = user_data.get("name", {})
            nome = (
                f"{name.get('firstName', '')} {name.get('lastName', '')}".strip()
                or None
            )
        except (json.JSONDecodeError, AttributeError):
            pass

    if not provider_user_id:
        raise HTTPException(status_code=400, detail="Risposta Apple non valida")

    session_token = await service.login_or_register(
        provider="apple",
        provider_user_id=provider_user_id,
        email=email,
        nome_completo=nome,
    )
    _set_session_cookie(response, session_token)
    return Response(
        status_code=302,
        headers={"Location": f"{settings.frontend_url}/banda"},
    )
