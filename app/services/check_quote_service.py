from __future__ import annotations

from decimal import Decimal

from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.iscrizione_repository import IscrizioneRepository
from app.repositories.socio_repository import SocioRepository
from app.schemas.check_quote import (
    CheckQuotaSocio,
    CheckQuoteResponse,
    CheckQuoteTotali,
    StatoQuota,
)


def _derive_stato(quota_attesa: Decimal, quota_versata: Decimal) -> StatoQuota:
    if quota_attesa == 0:
        return "NON_DOVUTA"
    if quota_versata > quota_attesa:
        return "SOVRAPPIU"
    if quota_versata == quota_attesa:
        return "OK"
    if quota_versata == 0:
        return "MANCANTE"
    return "PARZIALE"  # 0 < quota_versata < quota_attesa


class CheckQuoteService:
    def __init__(
        self,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
        socio_repo: SocioRepository,
        iscrizione_repo: IscrizioneRepository,
    ) -> None:
        self.cfg_repo = cfg_repo
        self.socio_repo = socio_repo
        self.iscrizione_repo = iscrizione_repo

    async def get_check_quote(self, banda_codice: int, anno: int) -> CheckQuoteResponse:
        cfg = await self.cfg_repo.get_by_banda_anno(banda_codice, anno)
        quota_attesa = Decimal(str(cfg.quota_annuale_attesa)) if cfg else Decimal(0)

        soci = await self.socio_repo.get_all_by_banda(banda_codice)
        versate = await self.iscrizione_repo.get_quote_versate_per_anno(
            banda_codice, anno
        )

        soci_resp: list[CheckQuotaSocio] = []
        totale_atteso = Decimal(0)
        totale_versato = Decimal(0)
        totale_mancante = Decimal(0)
        counts: dict[StatoQuota, int] = {
            "OK": 0,
            "PARZIALE": 0,
            "MANCANTE": 0,
            "SOVRAPPIU": 0,
            "NON_DOVUTA": 0,
        }

        for socio in soci:
            quota_versata = versate.get(socio.id, Decimal(0))
            differenza = quota_attesa - quota_versata
            stato = _derive_stato(quota_attesa, quota_versata)

            totale_atteso += quota_attesa
            totale_versato += quota_versata
            if differenza > 0:
                totale_mancante += differenza
            counts[stato] += 1

            soci_resp.append(
                CheckQuotaSocio(
                    socio_id=socio.id,
                    codice_socio=socio.codice_socio,
                    nome=socio.persona.nome,
                    cognome=socio.persona.cognome,
                    quota_attesa=quota_attesa,
                    quota_versata=quota_versata,
                    differenza=differenza,
                    stato=stato,
                )
            )

        return CheckQuoteResponse(
            banda_codice=banda_codice,
            anno=anno,
            quota_annuale_attesa=quota_attesa,
            soci=soci_resp,
            totali=CheckQuoteTotali(
                totale_atteso=totale_atteso,
                totale_versato=totale_versato,
                totale_mancante=totale_mancante,
                soci_ok=counts["OK"],
                soci_parziale=counts["PARZIALE"],
                soci_mancante=counts["MANCANTE"],
                soci_sovrappiu=counts["SOVRAPPIU"],
                soci_non_dovuta=counts["NON_DOVUTA"],
            ),
        )
