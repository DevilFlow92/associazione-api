from __future__ import annotations

from decimal import Decimal

from app.models.lookups import (
    Banda,
    SezioneRendiconto,
    SottovoceRendiconto,
    VoceRendiconto,
)
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
        banda_repo: LookupRepository[Banda],
    ) -> None:
        self.flusso_repo = flusso_repo
        self.cfg_repo = cfg_repo
        self.voce_contabilita_repo = voce_contabilita_repo
        self.sezione_repo = sezione_repo
        self.voce_rendiconto_repo = voce_rendiconto_repo
        self.sottovoce_repo = sottovoce_repo
        self.banda_repo = banda_repo

    async def get_rendiconto(self, banda_codice: int, anno: int) -> RendicontoResponse:
        cfg = await self.cfg_repo.get_by_banda_anno(banda_codice, anno)
        saldo_iniziale_cassa = (
            Decimal(str(cfg.saldo_iniziale_cassa)) if cfg else Decimal(0)
        )
        saldo_iniziale_banca = (
            Decimal(str(cfg.saldo_iniziale_banca)) if cfg else Decimal(0)
        )
        chiuso = cfg.chiuso if cfg else False

        banda = await self.banda_repo.get_by_codice(banda_codice)
        banda_nome = banda.descrizione if banda else f"Banda {banda_codice}"

        # Full Modello D skeleton from lookup tables (all sezioni/voci/sottovoci)
        struttura = await self.flusso_repo.get_struttura_rendiconto()

        # Flussi aggregation for this banda/anno
        rows = await self.flusso_repo.get_aggregati_per_rendiconto(banda_codice, anno)
        natura_dict = await self.flusso_repo.get_aggregati_per_natura(
            banda_codice, anno
        )

        # Build flat agg dict keyed by (sez_cod, voce_cod, sv_cod)
        agg: dict[tuple[int, int, int], Decimal] = {}
        for sez_cod, voce_cod, sv_cod, importo_signed in rows:
            key = (sez_cod, voce_cod, sv_cod)
            agg[key] = agg.get(key, Decimal(0)) + importo_signed

        # Identify sezioni to exclude from entrate/uscite totals
        sezione_descrizioni: dict[int, str] = {}
        for sez_cod, sez_desc, _vc, _vd, _sc, _sd in struttura:
            sezione_descrizioni[sez_cod] = sez_desc
        escluse_codici = {
            cod
            for cod, desc in sezione_descrizioni.items()
            if "fuori bilancio" in desc.lower() or "figurativi" in desc.lower()
        }

        # Compute entrate/uscite from raw rows (per-flusso signed importi)
        entrate = Decimal(0)
        uscite = Decimal(0)
        for sez_cod, _voce_cod, _sv_cod, importo_signed in rows:
            if sez_cod not in escluse_codici:
                if importo_signed > 0:
                    entrate += importo_signed
                elif importo_signed < 0:
                    uscite += -importo_signed

        # Walk skeleton: group by sezione → voce → sottovoci (already ordered)
        # Use ordered dicts to preserve codice ordering from the query
        sezioni_map: dict[
            int, tuple[str, dict[int, tuple[str, list[tuple[int, str]]]]]
        ] = {}
        for sez_cod, sez_desc, voce_cod, voce_desc, sv_cod, sv_desc in struttura:
            if sez_cod not in sezioni_map:
                sezioni_map[sez_cod] = (sez_desc, {})
            voci_map = sezioni_map[sez_cod][1]
            if voce_cod not in voci_map:
                voci_map[voce_cod] = (voce_desc, [])
            voci_map[voce_cod][1].append((sv_cod, sv_desc))

        sezioni_resp: list[SezioneRendicontoAggregato] = []
        for sez_cod, (sez_desc, voci_map) in sezioni_map.items():
            sezione_voci: list[VoceRendicontoAggregato] = []
            sezione_totale = Decimal(0)

            for voce_cod, (voce_desc, sv_list) in voci_map.items():
                voce_sottovoci: list[SottovoceRendicontoAggregato] = []
                voce_totale = Decimal(0)

                for sv_cod, sv_desc in sv_list:
                    sv_importo = agg.get((sez_cod, voce_cod, sv_cod), Decimal(0))
                    voce_sottovoci.append(
                        SottovoceRendicontoAggregato(
                            codice=sv_cod,
                            descrizione=sv_desc,
                            totale=sv_importo,
                        )
                    )
                    voce_totale += sv_importo

                sezione_voci.append(
                    VoceRendicontoAggregato(
                        codice=voce_cod,
                        descrizione=voce_desc,
                        totale=voce_totale,
                        sottovoci=voce_sottovoci,
                    )
                )
                sezione_totale += voce_totale

            sezioni_resp.append(
                SezioneRendicontoAggregato(
                    codice=sez_cod,
                    descrizione=sez_desc,
                    totale=sezione_totale,
                    voci=sezione_voci,
                )
            )

        saldo_finale_cassa = saldo_iniziale_cassa + natura_dict.get("cassa", Decimal(0))
        saldo_finale_banca = saldo_iniziale_banca + natura_dict.get("banca", Decimal(0))

        return RendicontoResponse(
            banda_codice=banda_codice,
            banda_nome=banda_nome,
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
