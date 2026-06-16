class FlussoCassaNotFoundError(Exception):
    def __init__(self, flusso_id: int) -> None:
        self.flusso_id = flusso_id
        super().__init__(f"Movimento di cassa con id {flusso_id} non trovato")
