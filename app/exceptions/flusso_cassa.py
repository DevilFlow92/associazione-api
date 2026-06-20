class FlussoCassaNotFoundError(Exception):
    def __init__(self, flusso_id: int) -> None:
        self.flusso_id = flusso_id
        super().__init__(f"Movimento di cassa con id {flusso_id} non trovato")


class AnnoChiusoError(Exception):
    def __init__(self, banda_codice: int, anno: int) -> None:
        self.banda_codice = banda_codice
        self.anno = anno
        super().__init__(
            f"Impossibile modificare il flusso: l'anno {anno} per la banda "
            f"{banda_codice} è chiuso."
        )
