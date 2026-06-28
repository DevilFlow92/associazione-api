from app.models.configurazione_banda_anno import ConfigurazioneBandaAnno  # noqa: F401
from app.models.contatto import Contatto  # noqa: F401
from app.models.documento import Documento  # noqa: F401
from app.models.esterno import Esterno  # noqa: F401
from app.models.flusso_cassa import FlussoCassa  # noqa: F401
from app.models.indirizzo import Indirizzo  # noqa: F401
from app.models.iscrizione import Iscrizione  # noqa: F401
from app.models.lookups import (  # noqa: F401
    Banda,
    Comune,
    NaturaFlusso,
    Provincia,
    Regione,
    RuoloBanda,
    RuoloContatto,
    SezioneRendiconto,
    SottovoceRendiconto,
    Stato,
    StatoIscrizione,
    Strumento,
    TipoDocumento,
    TipoIndirizzo,
    TipoSpartito,
    VoceRendiconto,
)
from app.models.oauth_account import OAuthAccount  # noqa: F401
from app.models.password_reset_token import PasswordResetToken  # noqa: F401
from app.models.permesso import Permesso  # noqa: F401
from app.models.persona import Persona  # noqa: F401
from app.models.relations import (  # noqa: F401
    bande_indirizzi,
    persone_indirizzi,
    ruoli_permessi,
    utenti_ruoli,
)
from app.models.ricevuta import Ricevuta  # noqa: F401
from app.models.ruolo import Ruolo  # noqa: F401
from app.models.servizio import Servizio  # noqa: F401
from app.models.sessione import Sessione  # noqa: F401
from app.models.socio import Socio  # noqa: F401
from app.models.spartito import Spartito  # noqa: F401
from app.models.template import Template  # noqa: F401
from app.models.utente import TipoUtente, Utente  # noqa: F401
from app.models.voce_contabilita import VoceContabilita  # noqa: F401
