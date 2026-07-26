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


class ProvaSenzaOrganicoError(Exception):
    def __init__(self, prova_id: int) -> None:
        self.prova_id = prova_id
        super().__init__(f"Prova con id {prova_id} non ha organico (nessuna Presenza)")


class ProvaSenzaRepertorioError(Exception):
    def __init__(self, prova_id: int) -> None:
        self.prova_id = prova_id
        super().__init__(f"Prova con id {prova_id} non ha repertorio (nessuna voce)")


class PersonaNonInOrganicoProvaError(Exception):
    def __init__(self, prova_id: int, persona_id: int) -> None:
        self.prova_id = prova_id
        self.persona_id = persona_id
        super().__init__(
            f"Persona con id {persona_id} non è in organico per la prova {prova_id}"
        )
