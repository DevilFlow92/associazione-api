from __future__ import annotations

from fastapi import HTTPException, status

from app.models.macro_sezione import MacroSezione
from app.models.utente import Utente


def require_write(user: Utente, macro_sezione: MacroSezione) -> None:
    """Impone il permesso di scrittura sulla macro-sezione genitrice.

    Permesso dinamico: dipende da ``macro_sezione.permesso_prefisso``
    (es. ``certificazioni:write``). I superuser bypassano sempre, come in
    ``app.api.deps.require_permission``.
    """
    if user.superuser:
        return
    richiesto = f"{macro_sezione.permesso_prefisso}:write"
    if richiesto not in user.permessi:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permesso richiesto: {richiesto}",
        )


def require_read(user: Utente, macro_sezione: MacroSezione) -> None:
    """Impone il permesso di lettura sulla macro-sezione genitrice.

    Stessa logica di require_write ma per ':read'. Introdotto in questa CR
    perché documenti.py, a differenza di sotto_cartelle.py nella CR
    precedente, ha bisogno di gating anche in lettura (i documenti contengono
    dati sensibili, le sotto-cartelle da sole no).
    """
    if user.superuser:
        return
    richiesto = f"{macro_sezione.permesso_prefisso}:read"
    if richiesto not in user.permessi:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permesso richiesto: {richiesto}",
        )
