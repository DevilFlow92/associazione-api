class ConfigurazioneBandaAnnoNotFoundError(Exception):
    def __init__(self, cfg_id: int) -> None:
        self.cfg_id = cfg_id
        super().__init__(f"Configurazione banda/anno con id {cfg_id} non trovata")


class ConfigurazioneBandaAnnoDuplicateError(Exception):
    def __init__(self, banda_codice: int, anno: int) -> None:
        super().__init__(
            f"Esiste già una configurazione per la banda {banda_codice} e l'anno {anno}"
        )


class ConfigurazioneBandaAnnoChiusaError(Exception):
    def __init__(self, cfg_id: int) -> None:
        self.cfg_id = cfg_id
        super().__init__(
            f"Configurazione con id {cfg_id} non modificabile: l'anno è chiuso"
        )
