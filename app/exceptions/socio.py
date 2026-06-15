class SocioNotFoundError(Exception):
    def __init__(self, socio_id: int) -> None:
        self.socio_id = socio_id
        super().__init__(f"Socio con id {socio_id} non trovato")


class SocioDuplicateCodiceError(Exception):
    def __init__(self, codice_socio: str, banda_codice: int) -> None:
        self.codice_socio = codice_socio
        self.banda_codice = banda_codice
        super().__init__(
            f"Codice socio {codice_socio} già presente per la banda {banda_codice}"
        )
