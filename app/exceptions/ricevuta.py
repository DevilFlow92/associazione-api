class RicevutaNotFoundError(Exception):
    def __init__(self, ricevuta_id: int) -> None:
        self.ricevuta_id = ricevuta_id
        super().__init__(f"Ricevuta con id {ricevuta_id} non trovata")
