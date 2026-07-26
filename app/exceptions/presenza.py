class PresenzaNotFoundError(Exception):
    def __init__(self, presenza_id: int) -> None:
        self.presenza_id = presenza_id
        super().__init__(f"Presenza con id {presenza_id} non trovata")


class PresenzaContainerMismatchError(Exception):
    def __init__(self) -> None:
        super().__init__(
            "Tutte le presenze indicate devono appartenere allo stesso "
            "servizio o alla stessa prova"
        )
