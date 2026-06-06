class SocioNotFoundError(Exception):
    def __init__(self, socio_id: int) -> None:
        self.socio_id = socio_id
        super().__init__(f"Socio con id {socio_id} non trovato")


class SocioDuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} già registrata")
