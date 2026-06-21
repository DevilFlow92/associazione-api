class IscrizioneNotFoundError(Exception):
    def __init__(self, iscrizione_id: int) -> None:
        self.iscrizione_id = iscrizione_id
        super().__init__(f"Iscrizione con id {iscrizione_id} non trovata")


class ConfigurazioneContabileMancanteError(Exception):
    def __init__(self, banda_codice: int, anno: int) -> None:
        self.banda_codice = banda_codice
        self.anno = anno
        super().__init__(
            f"Configurazione contabile mancante: imposta una voce per le quote "
            f"associative nella configurazione anno {anno}."
        )
