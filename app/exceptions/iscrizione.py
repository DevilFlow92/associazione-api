class IscrizioneNotFoundError(Exception):
    def __init__(self, iscrizione_id: int) -> None:
        self.iscrizione_id = iscrizione_id
        super().__init__(f"Iscrizione con id {iscrizione_id} non trovata")


class IscrizioneDuplicataError(Exception):
    def __init__(self, socio_id: int, anno: int) -> None:
        self.socio_id = socio_id
        self.anno = anno
        super().__init__(f"Socio {socio_id} già iscritto per l'anno {anno}")
