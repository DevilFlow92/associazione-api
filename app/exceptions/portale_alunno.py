class AccessoPortaleAlunnoNegatoError(Exception):
    """Il principal autenticato non ha titolo ad accedere a questa vista del
    portale alunno.

    Eccezione di dominio (non ``HTTPException``), sullo stesso pattern di
    ``AccessoSchedaAlunnoNegatoError``: tiene la logica di autorizzazione
    row-level testabile senza HTTP; il router la traduce in 403.
    """

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)
