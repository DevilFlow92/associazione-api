from __future__ import annotations

from decimal import Decimal

from app.models.lookups import SezioneRendiconto, SottovoceRendiconto, VoceRendiconto
from app.repositories.configurazione_banda_anno_repository import (
    ConfigurazioneBandaAnnoRepository,
)
from app.repositories.flusso_cassa_repository import FlussoCassaRepository
from app.repositories.lookup import LookupRepository
from app.repositories.voce_contabilita_repository import VoceContabilitaRepository
from app.schemas.rendiconto import (
    RendicontoMensileItem,
    RendicontoMensileResponse,
    RendicontoResponse,
    RendicontoTotali,
    SezioneRendicontoAggregato,
    SottovoceRendicontoAggregato,
    VoceRendicontoAggregato,
)


class RendicontoService:
    def __init__(
        self,
        flusso_repo: FlussoCassaRepository,
        cfg_repo: ConfigurazioneBandaAnnoRepository,
        voce_contabilita_repo: VoceContabilitaRepository,
        sezione_repo: LookupRepository[SezioneRendiconto],
        voce_rendiconto_repo: LookupRepository[VoceRendiconto],
        sottovoce_repo: LookupRepository[SottovoceRendiconto],
    ) -> None:
        self.flusso_repo = flusso_repo
        self.cfg_repo = cfg_repo
        self.voce_contabilita_repo = voce_contabilita_repo
        self.sezione_repo = sezione_repo
        self.voce_rendiconto_repo = voce_rendiconto_repo
        self.sottovoce_repo = sottovoce_repo

    async def get_rendiconto(self, banda_codice: int, anno: int) -> RendicontoResponse:
        cfg = await self.cfg_repo.get_by_banda_anno(banda_codice, anno)
        saldo_iniziale_cassa = (
            Decimal(str(cfg.saldo_iniziale_cassa)) if cfg else Decimal(0)
        )
        saldo_iniziale_banca = (
            Decimal(str(cfg.saldo_iniziale_banca)) if cfg else Decimal(0)
        )
        chiuso = cfg.chiuso if cfg else False

        # Structure driven by VoceContabilita for this banda: sezione → voce → sottovoci
        voci_contabilita = await self.voce_contabilita_repo.get_all(
            banda_codice=banda_codice, limit=10000
        )
        struct: dict[int, dict[int, set[int]]] = {}
        for vc in voci_contabilita:
            struct.setdefault(vc.sezione_rendiconto_codice, {}).setdefault(
                vc.voce_rendiconto_codice, set()
            ).add(vc.sottovoce_rendiconto_codice)

        # Flussi aggregation for this banda/anno
        rows = await self.flusso_repo.get_aggregati_per_rendiconto(banda_codice, anno)
        natura_dict = await self.flusso_repo.get_aggregati_per_natura(
            banda_codice, anno
        )

        # Build signed agg dict: sezione → voce → sottovoce → net importo
        agg: dict[int, dict[int, dict[int, Decimal]]] = {}
        for sez_cod, voce_cod, sv_cod, importo_signed in rows:
            agg.setdefault(sez_cod, {}).setdefault(voce_cod, {}).setdefault(
                sv_cod, Decimal(0)
            )
            agg[sez_cod][voce_cod][sv_cod] += importo_signed

        # Load lookup descriptions (ordered by codice)
        all_sezioni = {s.codice: s for s in await self.sezione_repo.get_all(limit=1000)}
        all_voci = {
            v.codice: v for v in await self.voce_rendiconto_repo.get_all(limit=1000)
        }
        all_sottovoci = {
            sv.codice: sv for sv in await self.sottovoce_repo.get_all(limit=1000)
        }

        fuori_bilancio_codici = {
            codice
            for codice, sez in all_sezioni.items()
            if sez.descrizione.lower() == "fuori bilancio"
        }

        # Compute entrate/uscite from raw rows (per-flusso signed importi)
        entrate = Decimal(0)
        uscite = Decimal(0)
        for sez_cod, _voce_cod, _sv_cod, importo_signed in rows:
            if sez_cod not in fuori_bilancio_codici:
                if importo_signed > 0:
                    entrate += importo_signed
                elif importo_signed < 0:
                    uscite += -importo_signed

        # Build nested sezioni response
        sezioni_resp: list[SezioneRendicontoAggregato] = []
        for sez_cod in sorted(struct.keys()):
            sezione = all_sezioni.get(sez_cod)
            if sezione is None:
                continue
            sezione_voci: list[VoceRendicontoAggregato] = []
            sezione_totale = Decimal(0)

            for voce_cod in sorted(struct[sez_cod].keys()):
                voce = all_voci.get(voce_cod)
                if voce is None:
                    continue
                voce_sottovoci: list[SottovoceRendicontoAggregato] = []
                voce_totale = Decimal(0)

                for sv_cod in sorted(struct[sez_cod][voce_cod]):
                    sottovoce = all_sottovoci.get(sv_cod)
                    if sottovoce is None:
                        continue
                    sv_importo = (
                        agg.get(sez_cod, {}).get(voce_cod, {}).get(sv_cod, Decimal(0))
                    )
                    voce_sottovoci.append(
                        SottovoceRendicontoAggregato(
                            codice=sottovoce.codice,
                            descrizione=sottovoce.descrizione,
                            totale=sv_importo,
                        )
                    )
                    voce_totale += sv_importo

                sezione_voci.append(
                    VoceRendicontoAggregato(
                        codice=voce.codice,
                        descrizione=voce.descrizione,
                        totale=voce_totale,
                        sottovoci=voce_sottovoci,
                    )
                )
                sezione_totale += voce_totale

            sezioni_resp.append(
                SezioneRendicontoAggregato(
                    codice=sezione.codice,
                    descrizione=sezione.descrizione,
                    totale=sezione_totale,
                    voci=sezione_voci,
                )
            )

        saldo_finale_cassa = saldo_iniziale_cassa + natura_dict.get("cassa", Decimal(0))
        saldo_finale_banca = saldo_iniziale_banca + natura_dict.get("banca", Decimal(0))

        return RendicontoResponse(
            banda_codice=banda_codice,
            anno=anno,
            chiuso=chiuso,
            saldo_iniziale_cassa=saldo_iniziale_cassa,
            saldo_iniziale_banca=saldo_iniziale_banca,
            sezioni=sezioni_resp,
            totali=RendicontoTotali(
                entrate=entrate,
                uscite=uscite,
                avanzo_disavanzo=entrate - uscite,
                saldo_finale_cassa=saldo_finale_cassa,
                saldo_finale_banca=saldo_finale_banca,
            ),
        )

    async def get_rendiconto_mensile(
        self, banda_codice: int, anno: int
    ) -> RendicontoMensileResponse:
        all_sezioni = {s.codice: s for s in await self.sezione_repo.get_all(limit=1000)}
        fuori_bilancio_codici = {
            codice
            for codice, sez in all_sezioni.items()
            if sez.descrizione.lower() == "fuori bilancio"
        }

        per_mese: dict[int, list[Decimal]] = {
            m: [Decimal(0), Decimal(0)] for m in range(1, 13)
        }

        rows = await self.flusso_repo.get_aggregati_mensili(banda_codice, anno)
        for mese, sez_cod, importo_signed in rows:
            if sez_cod in fuori_bilancio_codici:
                continue
            if importo_signed > 0:
                per_mese[mese][0] += importo_signed
            elif importo_signed < 0:
                per_mese[mese][1] += -importo_signed

        mensile = [
            RendicontoMensileItem(mese=m, entrate=per_mese[m][0], uscite=per_mese[m][1])
            for m in range(1, 13)
        ]
        return RendicontoMensileResponse(
            banda_codice=banda_codice, anno=anno, mensile=mensile
        )
