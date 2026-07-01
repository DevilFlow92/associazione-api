class SpartitoNotFoundError(Exception):
    def __init__(self, spartito_id: int) -> None:
        self.spartito_id = spartito_id
        super().__init__(f"Spartito con id {spartito_id} non trovato")


class NomeParteNotFoundError(Exception):
    def __init__(self, nome_parte_id: int) -> None:
        self.nome_parte_id = nome_parte_id
        super().__init__(f"NomeParte con id {nome_parte_id} non trovata")
