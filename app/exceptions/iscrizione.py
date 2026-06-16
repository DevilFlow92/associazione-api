class IscrizioneNotFoundError(Exception):
    def __init__(self, iscrizione_id: int) -> None:
        self.iscrizione_id = iscrizione_id
        super().__init__(f"Iscrizione con id {iscrizione_id} non trovata")
