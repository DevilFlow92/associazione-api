class LezioneNotFoundError(Exception):
    def __init__(self, lezione_id: int) -> None:
        self.lezione_id = lezione_id
        super().__init__(f"Lezione con id {lezione_id} non trovata")
