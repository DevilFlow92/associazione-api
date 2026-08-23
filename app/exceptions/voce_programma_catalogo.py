class VoceProgrammaCatalogoNotFoundError(Exception):
    def __init__(self, voce_id: int) -> None:
        self.voce_id = voce_id
        super().__init__(f"Voce programma catalogo con id {voce_id} non trovata")


class VoceProgrammaCatalogoDuplicataError(Exception):
    """Esiste già una voce con lo stesso testo per lo stesso tipo corso."""

    def __init__(self, tipo_corso_codice: int, testo: str) -> None:
        self.tipo_corso_codice = tipo_corso_codice
        self.testo = testo
        super().__init__(
            f"Voce con testo {testo!r} già esistente per il tipo corso "
            f"{tipo_corso_codice}"
        )
