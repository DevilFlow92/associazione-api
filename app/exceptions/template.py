class TemplateNotFoundError(Exception):
    def __init__(self, template_id: int) -> None:
        self.template_id = template_id
        super().__init__(f"Template con id {template_id} non trovato")


class TemplateTipoNonValidoError(Exception):
    def __init__(self, mime_type: str) -> None:
        self.mime_type = mime_type
        super().__init__(f"Tipo file non supportato: {mime_type}. Solo PDF accettati.")
