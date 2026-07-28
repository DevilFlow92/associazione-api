class CorsoNotFoundError(Exception):
    def __init__(self, corso_id: int) -> None:
        self.corso_id = corso_id
        super().__init__(f"Corso con id {corso_id} non trovato")
