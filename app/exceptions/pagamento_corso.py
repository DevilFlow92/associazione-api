class PagamentoCorsoNotFoundError(Exception):
    def __init__(self, pagamento_corso_id: int) -> None:
        self.pagamento_corso_id = pagamento_corso_id
        super().__init__(f"Pagamento corso con id {pagamento_corso_id} non trovato")


class ConfigurazioneContabileCorsiMancanteError(Exception):
    def __init__(self, banda_codice: int, anno: int) -> None:
        self.banda_codice = banda_codice
        self.anno = anno
        super().__init__(
            f"Configurazione contabile mancante: imposta una voce per le rette "
            f"corsi nella configurazione anno {anno}."
        )
