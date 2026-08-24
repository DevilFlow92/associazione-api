from collections.abc import Collection


class SchedaAlunnoMaterialeNotFoundError(Exception):
    """Nessun materiale con questo id per questa scheda alunno.

    Sollevata anche quando il materiale esiste ma appartiene a un'altra
    scheda: l'endpoint è annidato sotto
    ``/schede-alunno/{scheda_alunno_id}/materiali``, stesso trattamento già
    in uso per ``SchedaAlunnoVoceNotFoundError``.
    """

    def __init__(self, materiale_id: int) -> None:
        self.materiale_id = materiale_id
        super().__init__(
            f"Materiale {materiale_id} non trovato per questa scheda alunno"
        )


class EstensioneMaterialeNonAmmessaError(Exception):
    """L'estensione del file caricato non è nella whitelist ammessa."""

    def __init__(self, estensione: str, estensioni_ammesse: Collection[str]) -> None:
        self.estensione = estensione
        self.estensioni_ammesse = estensioni_ammesse
        ammesse = ", ".join(sorted(estensioni_ammesse))
        super().__init__(
            f"Estensione file '{estensione}' non ammessa. Estensioni valide: {ammesse}"
        )


class MaterialeTroppoGrandeError(Exception):
    """Il file caricato supera il limite di dimensione consentito."""

    def __init__(self, dimensione_bytes: int, limite_bytes: int) -> None:
        self.dimensione_bytes = dimensione_bytes
        self.limite_bytes = limite_bytes
        super().__init__(
            f"File di {dimensione_bytes} byte supera il limite di {limite_bytes} byte"
        )


class MaterialeNonFileError(Exception):
    """Il materiale richiesto in download è un link esterno, non un file."""

    def __init__(self, materiale_id: int) -> None:
        self.materiale_id = materiale_id
        super().__init__(
            f"Il materiale {materiale_id} è un link esterno: usa l'url direttamente"
        )
