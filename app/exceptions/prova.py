class ProvaNotFoundError(Exception):
    def __init__(self, prova_id: int) -> None:
        self.prova_id = prova_id
        super().__init__(f"Prova con id {prova_id} non trovata")
