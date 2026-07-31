class AllievoNotFoundError(Exception):
    def __init__(self, allievo_id: int) -> None:
        self.allievo_id = allievo_id
        super().__init__(f"Allievo con id {allievo_id} non trovato")


class AllievoDuplicateCodiceError(Exception):
    def __init__(self, codice_allievo: str) -> None:
        self.codice_allievo = codice_allievo
        super().__init__(f"Codice allievo {codice_allievo} già presente")


class AllievoPersonaAlreadyLinkedError(Exception):
    def __init__(self, persona_id: int) -> None:
        self.persona_id = persona_id
        super().__init__(f"Persona con id {persona_id} è già collegata a un allievo")
