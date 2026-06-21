class FlussoCassaNotFoundError(Exception):
    def __init__(self, flusso_id: int) -> None:
        self.flusso_id = flusso_id
        super().__init__(f"Movimento di cassa con id {flusso_id} non trovato")


class AnnoChiusoError(Exception):
    def __init__(self, banda_codice: int, anno: int) -> None:
        self.banda_codice = banda_codice
        self.anno = anno
        super().__init__(
            f"Impossibile modificare il flusso: l'anno {anno} per la banda "
            f"{banda_codice} è chiuso."
        )


class NaturaFlussoNotFoundError(Exception):
    def __init__(self, codice: int) -> None:
        self.codice = codice
        super().__init__(f"Natura flusso con codice {codice} non trovata")


class TrasferimentoNaturaUgualeError(Exception):
    def __init__(self, codice: int) -> None:
        self.codice = codice
        super().__init__(
            "La natura di origine e quella di destinazione di un trasferimento "
            f"devono essere diverse (entrambe: {codice})."
        )


class FlussoTrasferimentoNonModificabileError(Exception):
    def __init__(self, flusso_id: int) -> None:
        self.flusso_id = flusso_id
        super().__init__(
            "Impossibile modificare un trasferimento. Eliminarlo e ricrearlo."
        )
