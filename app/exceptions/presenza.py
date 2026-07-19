class PresenzaNotFoundError(Exception):
    def __init__(self, presenza_id: int) -> None:
        self.presenza_id = presenza_id
        super().__init__(f"Presenza con id {presenza_id} non trovata")
