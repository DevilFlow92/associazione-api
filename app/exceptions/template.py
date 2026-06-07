class TemplateNotFoundError(Exception):
    def __init__(self, template_id: int) -> None:
        self.template_id = template_id
        super().__init__(f"Template con id {template_id} non trovato")
