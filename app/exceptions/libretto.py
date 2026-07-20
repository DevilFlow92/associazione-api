class ServizioSenzaOrganicoError(Exception):
    def __init__(self, servizio_id: int) -> None:
        self.servizio_id = servizio_id
        super().__init__(
            f"Servizio con id {servizio_id} non ha organico (nessuna Presenza)"
        )


class ServizioSenzaRepertorioError(Exception):
    def __init__(self, servizio_id: int) -> None:
        self.servizio_id = servizio_id
        super().__init__(
            f"Servizio con id {servizio_id} non ha repertorio (nessuna voce)"
        )


class PersonaNonInOrganicoError(Exception):
    def __init__(self, servizio_id: int, persona_id: int) -> None:
        self.servizio_id = servizio_id
        self.persona_id = persona_id
        super().__init__(
            f"Persona con id {persona_id} non è in organico per il servizio "
            f"{servizio_id}"
        )
