"""RBAC guard coverage: the deny/allow branches the superuser-by-default test
client never exercises (require_permission, require_superuser, 401 boundary)."""

from __future__ import annotations

from collections.abc import Collection

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.api.deps import get_current_user, require_permission, require_superuser
from app.models.permesso import Permesso
from app.models.ruolo import Ruolo
from app.models.utente import TipoUtente, Utente
from main import app


def _user(*, superuser: bool = False, permessi: Collection[str] = ()) -> Utente:
    ruoli: list[Ruolo] = []
    if permessi:
        ruoli = [
            Ruolo(
                nome="test",
                permessi=[Permesso(codice=c, descrizione=c) for c in permessi],
            )
        ]
    return Utente(
        id=1,
        tipo=TipoUtente.UMANO,
        email="rbac@example.com",
        superuser=superuser,
        ruoli=ruoli,
    )


async def test_require_permission_allows_superuser() -> None:
    guard = require_permission("contabilita:read")
    user = _user(superuser=True)
    assert await guard(user=user) is user


async def test_require_permission_allows_user_with_permission() -> None:
    guard = require_permission("contabilita:read")
    user = _user(permessi={"contabilita:read"})
    assert await guard(user=user) is user


async def test_require_permission_denies_user_without_permission() -> None:
    guard = require_permission("contabilita:read")
    user = _user(permessi={"contabilita:write"})
    with pytest.raises(HTTPException) as exc:
        await guard(user=user)
    assert exc.value.status_code == 403


def test_require_superuser_allows_superuser() -> None:
    user = _user(superuser=True)
    assert require_superuser(user=user) is user


def test_require_superuser_denies_non_superuser() -> None:
    user = _user()
    with pytest.raises(HTTPException) as exc:
        require_superuser(user=user)
    assert exc.value.status_code == 403


async def test_protected_endpoint_forbidden_without_permission(
    client: AsyncClient,
) -> None:
    app.dependency_overrides[get_current_user] = lambda: _user(
        permessi={"contabilita:write"}
    )
    r = await client.get("/api/v1/contabilita/check-quote/?banda_codice=1&anno=2023")
    assert r.status_code == 403


async def test_protected_endpoint_requires_authentication(
    client: AsyncClient,
) -> None:
    app.dependency_overrides.pop(get_current_user, None)
    r = await client.get("/api/v1/contabilita/check-quote/?banda_codice=1&anno=2023")
    assert r.status_code == 401
