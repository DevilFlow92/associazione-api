class VoceContabilitaNotFoundError(Exception):
    def __init__(self, voce_contabilita_id: int) -> None:
        self.voce_contabilita_id = voce_contabilita_id
        super().__init__(f"Voce contabilità con id {voce_contabilita_id} non trovata")


class VoceContabilitaHasFlussiError(Exception):
    """La voce di contabilità ha movimenti di cassa collegati."""

    def __init__(self, voce_contabilita_id: int) -> None:
        self.voce_contabilita_id = voce_contabilita_id
        super().__init__(
            f"Voce contabilità con id {voce_contabilita_id} non eliminabile: "
            "esistono movimenti di cassa collegati"
        )
