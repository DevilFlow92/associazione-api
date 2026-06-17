class InvalidCredentialsError(Exception):
    """Email/password errati, oppure credenziali non utilizzabili."""

    def __init__(self) -> None:
        super().__init__("Credenziali non valide")


class InactiveUserError(Exception):
    def __init__(self) -> None:
        super().__init__("Utente disattivato")


class InvalidTokenError(Exception):
    """Token (JWT o sessione) assente, malformato, scaduto o revocato."""

    def __init__(self, message: str = "Token non valido o scaduto") -> None:
        super().__init__(message)


class PermissionDeniedError(Exception):
    def __init__(self, permesso: str) -> None:
        self.permesso = permesso
        super().__init__(f"Permesso richiesto: {permesso}")
