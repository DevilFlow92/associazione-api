class IscrizioneCorsoNotFoundError(Exception):
    def __init__(self, iscrizione_corso_id: int) -> None:
        self.iscrizione_corso_id = iscrizione_corso_id
        super().__init__(f"Iscrizione corso con id {iscrizione_corso_id} non trovata")
