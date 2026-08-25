class CodiceProgressivoError(Exception):
    """Impossibile generare un codice progressivo libero per l'entità e la
    banda indicate dopo i tentativi massimi consentiti."""

    def __init__(self, entita: str, banda_codice: int, tentativi: int) -> None:
        self.entita = entita
        self.banda_codice = banda_codice
        self.tentativi = tentativi
        super().__init__(
            f"Impossibile generare un codice {entita} libero per la banda "
            f"{banda_codice} dopo {tentativi} tentativi"
        )
