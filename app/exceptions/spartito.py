class SpartitoNotFoundError(Exception):
    def __init__(self, spartito_id: int) -> None:
        self.spartito_id = spartito_id
        super().__init__(f"Spartito con id {spartito_id} non trovato")
