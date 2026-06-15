class LookupNotFoundError(Exception):
    """Una voce di tabella dimensione (lookup) non è stata trovata."""

    def __init__(self, label: str, codice: int) -> None:
        self.label = label
        self.codice = codice
        super().__init__(f"{label} con codice {codice} non trovato")


class LookupDuplicateCodiceError(Exception):
    """Il codice di una voce di lookup è già presente."""

    def __init__(self, label: str, codice: int) -> None:
        self.label = label
        self.codice = codice
        super().__init__(f"{label} con codice {codice} già esistente")
