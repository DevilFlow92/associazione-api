class CommittenteNotFoundError(Exception):
    def __init__(self, committente_id: int) -> None:
        self.committente_id = committente_id
        super().__init__(f"Committente con id {committente_id} non trovato")


class CommittenteHasServiziError(Exception):
    """Il committente non può essere eliminato perché ha servizi collegati."""

    def __init__(self, committente_id: int) -> None:
        self.committente_id = committente_id
        super().__init__(
            f"Committente con id {committente_id} non eliminabile: "
            "esistono servizi collegati"
        )
