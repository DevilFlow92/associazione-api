from __future__ import annotations

from associazione_toolkit.pagination import PagedResponse, PageParams, paginate

from app.exceptions.utente import (
    PermessoNotFoundError,
    RuoloDuplicateNomeError,
    RuoloNotFoundError,
)
from app.repositories.permesso_repository import PermessoRepository
from app.repositories.ruolo_repository import RuoloRepository
from app.schemas.ruolo import RuoloCreate, RuoloResponse, RuoloUpdate


class RuoloService:
    def __init__(
        self, repo: RuoloRepository, permesso_repo: PermessoRepository
    ) -> None:
        self.repo = repo
        self.permesso_repo = permesso_repo

    async def _resolve_permessi(self, codici: list[str]) -> list:
        permessi = await self.permesso_repo.get_by_codici(codici)
        trovati = {p.codice for p in permessi}
        for codice in codici:
            if codice not in trovati:
                raise PermessoNotFoundError(codice)
        return permessi

    async def get_all(self, params: PageParams) -> PagedResponse[RuoloResponse]:
        ruoli = await self.repo.get_all(offset=params.offset, limit=params.limit)
        total = await self.repo.count_all()
        items = [RuoloResponse.model_validate(r) for r in ruoli]
        return paginate(items, total, params)

    async def get_by_id(self, ruolo_id: int) -> RuoloResponse:
        ruolo = await self.repo.get_by_id(ruolo_id)
        if not ruolo:
            raise RuoloNotFoundError(ruolo_id)
        return RuoloResponse.model_validate(ruolo)

    async def create(self, data: RuoloCreate) -> RuoloResponse:
        existing = await self.repo.get_by_nome(data.nome, data.banda_codice)
        if existing:
            raise RuoloDuplicateNomeError(data.nome, data.banda_codice)
        permessi = await self._resolve_permessi(data.permessi)
        ruolo = await self.repo.create(
            nome=data.nome,
            descrizione=data.descrizione,
            banda_codice=data.banda_codice,
            permessi=permessi,
        )
        return RuoloResponse.model_validate(ruolo)

    async def update(self, ruolo_id: int, data: RuoloUpdate) -> RuoloResponse:
        ruolo = await self.repo.get_by_id(ruolo_id)
        if not ruolo:
            raise RuoloNotFoundError(ruolo_id)
        fields = data.model_dump(exclude_unset=True, exclude={"permessi"})
        nome = fields.get("nome", ruolo.nome)
        banda = fields.get("banda_codice", ruolo.banda_codice)
        if "nome" in fields or "banda_codice" in fields:
            existing = await self.repo.get_by_nome(nome, banda)
            if existing and existing.id != ruolo_id:
                raise RuoloDuplicateNomeError(nome, banda)
        permessi = (
            await self._resolve_permessi(data.permessi)
            if data.permessi is not None
            else None
        )
        updated = await self.repo.update(ruolo, fields=fields, permessi=permessi)
        return RuoloResponse.model_validate(updated)

    async def delete(self, ruolo_id: int) -> None:
        ruolo = await self.repo.get_by_id(ruolo_id)
        if not ruolo:
            raise RuoloNotFoundError(ruolo_id)
        await self.repo.delete(ruolo)
