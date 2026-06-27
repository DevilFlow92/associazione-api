"""Invio email transazionali via Resend.

Modulo puro (nessuna dipendenza dal DB). I chiamanti gestiscono gli errori:
l'invio email è best-effort e non deve far fallire l'operazione applicativa
(reset password, registrazione).
"""

from __future__ import annotations

import resend

from app.core.config import settings


def _configure() -> None:
    """Configura la chiave API. Solleva se non impostata."""
    if not settings.resend_api_key:
        raise RuntimeError("RESEND_API_KEY non configurata")
    resend.api_key = settings.resend_api_key


def send_password_reset(to: str, reset_url: str) -> None:
    """Invia l'email di reset password. Best-effort: il caller gestisce gli errori."""
    _configure()
    html = (
        "<p>Hai richiesto il reset della password per il tuo account BandApp.</p>"
        f'<p><a href="{reset_url}">Clicca qui per reimpostare la password</a></p>'
        "<p>Il link scade tra 1 ora. Se non hai richiesto il reset, "
        "ignora questa email.</p>"
    )
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": [to],
            "subject": "BandApp — Reimposta la tua password",
            "html": html,
        }
    )


def send_registration_notification(to: list[str], nome_utente: str, banda: str) -> None:
    """Notifica gli amministratori di una nuova auto-registrazione."""
    if not to:
        return
    _configure()
    html = (
        "<p>Un nuovo utente si è registrato a BandApp.</p>"
        "<ul>"
        f"<li><strong>Nome:</strong> {nome_utente}</li>"
        f"<li><strong>Banda:</strong> {banda}</li>"
        "</ul>"
        "<p>L'utente ha ricevuto il ruolo <em>Ospite</em> ed è già attivo.</p>"
    )
    resend.Emails.send(
        {
            "from": settings.email_from,
            "to": to,
            "subject": f"BandApp — Nuova registrazione per {banda}",
            "html": html,
        }
    )
