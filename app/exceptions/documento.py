class DocumentoNotFoundError(Exception):
    def __init__(self, documento_id: int) -> None:
        self.documento_id = documento_id
        super().__init__(f"Documento con id {documento_id} non trovato")


class DocumentoTipoNonValidoError(Exception):
    def __init__(self, mime_type: str) -> None:
        self.mime_type = mime_type
        super().__init__(f"Tipo file non supportato: {mime_type}. Solo PDF accettati.")


class DocumentoSottoCartellaNotFoundError(Exception):
    def __init__(self, sotto_cartella_id: int) -> None:
        self.sotto_cartella_id = sotto_cartella_id
        super().__init__(f"SottoCartella con id {sotto_cartella_id} non trovata")
