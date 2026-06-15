class ContattoNotFoundError(Exception):
    def __init__(self, contatto_id: int) -> None:
        self.contatto_id = contatto_id
        super().__init__(f"Contatto con id {contatto_id} non trovato")
