class ServizioNotFoundError(Exception):
    def __init__(self, servizio_id: int) -> None:
        self.servizio_id = servizio_id
        super().__init__(f"Servizio con id {servizio_id} non trovato")


class ServizioHasRicevuteError(Exception):
    """Il servizio non può essere eliminato perché ha ricevute collegate."""

    def __init__(self, servizio_id: int) -> None:
        self.servizio_id = servizio_id
        super().__init__(
            f"Servizio con id {servizio_id} non eliminabile: "
            "esistono ricevute collegate"
        )
