class PersonaNotFoundError(Exception):
    def __init__(self, persona_id: int) -> None:
        self.persona_id = persona_id
        super().__init__(f"Persona con id {persona_id} non trovata")


class PersonaHasDependentsError(Exception):
    """La persona non può essere eliminata perché è ancora socio o esterno."""

    def __init__(self, persona_id: int) -> None:
        self.persona_id = persona_id
        super().__init__(
            f"Persona con id {persona_id} non eliminabile: "
            "esistono soci o esterni collegati"
        )
