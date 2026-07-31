class SchedaAlunnoNotFoundError(Exception):
    def __init__(self, scheda_alunno_id: int) -> None:
        self.scheda_alunno_id = scheda_alunno_id
        super().__init__(f"Scheda alunno con id {scheda_alunno_id} non trovata")


class SchedaAlunnoIscrizioneNotFoundError(Exception):
    """Nessuna scheda esiste (ancora) per l'iscrizione indicata."""

    def __init__(self, iscrizione_corso_id: int) -> None:
        self.iscrizione_corso_id = iscrizione_corso_id
        super().__init__(
            f"Nessuna scheda alunno per l'iscrizione corso {iscrizione_corso_id}"
        )


class SchedaAlunnoDuplicataError(Exception):
    """Una scheda per quell'iscrizione esiste già (vincolo UNIQUE)."""

    def __init__(self, iscrizione_corso_id: int) -> None:
        self.iscrizione_corso_id = iscrizione_corso_id
        super().__init__(
            f"Esiste già una scheda alunno per l'iscrizione corso {iscrizione_corso_id}"
        )


class AccessoSchedaAlunnoNegatoError(Exception):
    """Il principal autenticato non ha titolo ad accedere a questa scheda.

    Eccezione di dominio (non ``HTTPException``) per tenere la logica di
    autorizzazione row-level testabile senza HTTP; i router la traducono in 403.
    """

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)
