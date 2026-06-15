class EsternoNotFoundError(Exception):
    def __init__(self, esterno_id: int) -> None:
        self.esterno_id = esterno_id
        super().__init__(f"Esterno con id {esterno_id} non trovato")


class EsternoDuplicateCodiceError(Exception):
    def __init__(self, codice_esterno: str) -> None:
        self.codice_esterno = codice_esterno
        super().__init__(f"Codice esterno {codice_esterno} già presente")
