class UtenteNotFoundError(Exception):
    def __init__(self, utente_id: int) -> None:
        self.utente_id = utente_id
        super().__init__(f"Utente con id {utente_id} non trovato")


class UtenteDuplicateEmailError(Exception):
    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"Email {email} già registrata")


class RuoloNotFoundError(Exception):
    def __init__(self, ruolo_id: int) -> None:
        self.ruolo_id = ruolo_id
        super().__init__(f"Ruolo con id {ruolo_id} non trovato")


class RuoloDuplicateNomeError(Exception):
    def __init__(self, nome: str, banda_codice: int | None) -> None:
        self.nome = nome
        self.banda_codice = banda_codice
        super().__init__(f"Ruolo {nome} già presente per la banda {banda_codice}")


class PermessoNotFoundError(Exception):
    def __init__(self, codice: str) -> None:
        self.codice = codice
        super().__init__(f"Permesso {codice} non trovato")
