class RepertorioItemNotFoundError(Exception):
    def __init__(self, repertorio_item_id: int) -> None:
        self.repertorio_item_id = repertorio_item_id
        super().__init__(f"Voce di repertorio con id {repertorio_item_id} non trovata")
