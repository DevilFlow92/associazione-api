from __future__ import annotations

from app.core.logging import get_logger
from app.models.utente import TipoUtente, Utente
from app.repositories.oauth_account_repository import OAuthAccountRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.repositories.sessione_repository import SessioneRepository
from app.repositories.utente_repository import UtenteRepository
from app.services.auth_service import AuthService

logger = get_logger(__name__)


class OAuthService:
    """Gestisce il linking/creazione utente dopo il callback OAuth2.

    Flusso:
    1. Cerca un OAuthAccount per (provider, provider_user_id).
       → trovato: apre una sessione per l'utente collegato.
    2. Non trovato: cerca un Utente per email.
       → trovato: collega il provider all'utente esistente, apre sessione.
    3. Non trovato: crea un nuovo Utente (tipo=umano, ruolo Ospite) e
       l'OAuthAccount associato, apre sessione.
    """

    def __init__(
        self,
        utente_repo: UtenteRepository,
        oauth_repo: OAuthAccountRepository,
        sessione_repo: SessioneRepository,
        ruolo_repo: RuoloRepository,
        auth_service: AuthService,
    ) -> None:
        self.utente_repo = utente_repo
        self.oauth_repo = oauth_repo
        self.sessione_repo = sessione_repo
        self.ruolo_repo = ruolo_repo
        self.auth_service = auth_service

    async def login_or_register(
        self,
        provider: str,
        provider_user_id: str,
        email: str | None,
        nome_completo: str | None,
        banda_codice: int | None = None,
    ) -> str:
        """Ritorna il session token opaco da impostare nel cookie."""
        utente: Utente | None = None

        # 1. OAuthAccount già esistente
        existing_oauth = await self.oauth_repo.get_by_provider(
            provider, provider_user_id
        )
        if existing_oauth:
            utente = existing_oauth.utente
            logger.info("oauth_login", provider=provider, utente_id=utente.id)
            return await self.auth_service._open_session(utente)

        # 2. Utente esistente per email → link
        if email:
            utente = await self.utente_repo.get_by_email(email)

        if utente is None:
            # 3. Crea nuovo utente con ruolo Ospite
            ospite_ruolo = await self.ruolo_repo.get_by_nome(
                "Ospite", banda_codice=None
            )
            utente = Utente(
                tipo=TipoUtente.UMANO,
                email=email or f"{provider}_{provider_user_id}@noemail.local",
                nome_completo=nome_completo,
                attivo=True,
                superuser=False,
            )
            if ospite_ruolo:
                utente.ruoli = [ospite_ruolo]
            self.utente_repo.db.add(utente)
            await self.utente_repo.db.flush()
            logger.info("oauth_register", provider=provider, utente_id=utente.id)
        else:
            logger.info("oauth_link", provider=provider, utente_id=utente.id)

        await self.oauth_repo.create(
            utente_id=utente.id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
        )
        await self.utente_repo.db.commit()
        return await self.auth_service._open_session(utente)
