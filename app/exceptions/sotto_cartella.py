class SottoCartellaNotFoundError(Exception):
    def __init__(self, sotto_cartella_id: int) -> None:
        self.sotto_cartella_id = sotto_cartella_id
        super().__init__(f"Sotto-cartella con id {sotto_cartella_id} non trovata")


class SottoCartellaDuplicateNomeError(Exception):
    def __init__(self, nome: str, macro_sezione_codice: int) -> None:
        self.nome = nome
        self.macro_sezione_codice = macro_sezione_codice
        msg = (
            f"Sotto-cartella '{nome}' già presente nella macro-sezione "
            f"{macro_sezione_codice}"
        )
        super().__init__(msg)


class SottoCartellaMacroSezioneNotFoundError(Exception):
    def __init__(self, macro_sezione_codice: int) -> None:
        self.macro_sezione_codice = macro_sezione_codice
        super().__init__(f"Macro-sezione con codice {macro_sezione_codice} non trovata")
