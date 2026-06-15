class IndirizzoNotFoundError(Exception):
    def __init__(self, indirizzo_id: int) -> None:
        self.indirizzo_id = indirizzo_id
        super().__init__(f"Indirizzo con id {indirizzo_id} non trovato")
