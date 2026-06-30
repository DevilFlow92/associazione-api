from __future__ import annotations

from app.repositories.sotto_cartella_repository import MacroSezioneRepository
from app.schemas.macro_sezione import MacroSezioneResponse


class MacroSezioneService:
    def __init__(self, repo: MacroSezioneRepository) -> None:
        self.repo = repo

    async def get_all(self) -> list[MacroSezioneResponse]:
        macro_sezioni = await self.repo.get_all()
        return [MacroSezioneResponse.model_validate(m) for m in macro_sezioni]
