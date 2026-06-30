from __future__ import annotations

from app.exceptions.sotto_cartella import (
    SottoCartellaDuplicateNomeError,
    SottoCartellaMacroSezioneNotFoundError,
    SottoCartellaNotFoundError,
)
from app.models.utente import Utente
from app.repositories.sotto_cartella_repository import (
    MacroSezioneRepository,
    SottoCartellaRepository,
)
from app.schemas.sotto_cartella import (
    SottoCartellaCreate,
    SottoCartellaResponse,
    SottoCartellaUpdate,
)
from app.services.permessi_archivio import require_write


class SottoCartellaService:
    def __init__(
        self,
        repo: SottoCartellaRepository,
        macro_sezione_repo: MacroSezioneRepository,
    ) -> None:
        self.repo = repo
        self.macro_sezione_repo = macro_sezione_repo

    async def get_all_for_macro_sezione(
        self, macro_sezione_codice: int
    ) -> list[SottoCartellaResponse]:
        macro_sezione = await self.macro_sezione_repo.get_by_codice(
            macro_sezione_codice
        )
        if not macro_sezione:
            raise SottoCartellaMacroSezioneNotFoundError(macro_sezione_codice)
        items = await self.repo.get_all_by_macro_sezione(macro_sezione_codice)
        return [SottoCartellaResponse.model_validate(i) for i in items]

    async def create(
        self, data: SottoCartellaCreate, user: Utente
    ) -> SottoCartellaResponse:
        macro_sezione = await self.macro_sezione_repo.get_by_codice(
            data.macro_sezione_codice
        )
        if not macro_sezione:
            raise SottoCartellaMacroSezioneNotFoundError(data.macro_sezione_codice)
        require_write(user, macro_sezione)
        existing = await self.repo.get_by_nome(data.nome, data.macro_sezione_codice)
        if existing:
            raise SottoCartellaDuplicateNomeError(data.nome, data.macro_sezione_codice)
        obj = await self.repo.create(
            nome=data.nome, macro_sezione_codice=data.macro_sezione_codice
        )
        return SottoCartellaResponse.model_validate(obj)

    async def update(
        self, id: int, data: SottoCartellaUpdate, user: Utente
    ) -> SottoCartellaResponse:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise SottoCartellaNotFoundError(id)
        macro_sezione = await self.macro_sezione_repo.get_by_codice(
            obj.macro_sezione_codice
        )
        if not macro_sezione:
            raise SottoCartellaMacroSezioneNotFoundError(obj.macro_sezione_codice)
        require_write(user, macro_sezione)
        if data.nome is not None and data.nome != obj.nome:
            existing = await self.repo.get_by_nome(data.nome, obj.macro_sezione_codice)
            if existing and existing.id != id:
                raise SottoCartellaDuplicateNomeError(
                    data.nome, obj.macro_sezione_codice
                )
            obj = await self.repo.update(obj, data.nome)
        return SottoCartellaResponse.model_validate(obj)

    async def delete(self, id: int, user: Utente) -> None:
        obj = await self.repo.get_by_id(id)
        if not obj:
            raise SottoCartellaNotFoundError(id)
        macro_sezione = await self.macro_sezione_repo.get_by_codice(
            obj.macro_sezione_codice
        )
        if not macro_sezione:
            raise SottoCartellaMacroSezioneNotFoundError(obj.macro_sezione_codice)
        require_write(user, macro_sezione)
        await self.repo.delete(obj)
