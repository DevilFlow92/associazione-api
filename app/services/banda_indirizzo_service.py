from __future__ import annotations

from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.lookup import LookupNotFoundError
from app.repositories.banda_indirizzo_repository import BandaIndirizzoRepository
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.schemas.indirizzo import IndirizzoResponse


class BandaIndirizzoService:
    """Business logic per la relazione molti-a-molti banda↔indirizzo."""

    def __init__(
        self, repo: BandaIndirizzoRepository, indirizzo_repo: IndirizzoRepository
    ) -> None:
        self.repo = repo
        self.indirizzo_repo = indirizzo_repo

    async def get_indirizzi(self, banda_codice: int) -> list[IndirizzoResponse]:
        banda = await self.repo.get_with_indirizzi(banda_codice)
        if not banda:
            raise LookupNotFoundError("Banda", banda_codice)
        return [IndirizzoResponse.model_validate(i) for i in banda.indirizzi]

    async def add_indirizzo(
        self, banda_codice: int, indirizzo_id: int
    ) -> list[IndirizzoResponse]:
        banda = await self.repo.get_with_indirizzi(banda_codice)
        if not banda:
            raise LookupNotFoundError("Banda", banda_codice)
        indirizzo = await self.indirizzo_repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        await self.repo.add_indirizzo(banda, indirizzo)
        return [IndirizzoResponse.model_validate(i) for i in banda.indirizzi]

    async def remove_indirizzo(self, banda_codice: int, indirizzo_id: int) -> None:
        banda = await self.repo.get_with_indirizzi(banda_codice)
        if not banda:
            raise LookupNotFoundError("Banda", banda_codice)
        indirizzo = await self.indirizzo_repo.get_by_id(indirizzo_id)
        if not indirizzo:
            raise IndirizzoNotFoundError(indirizzo_id)
        await self.repo.remove_indirizzo(banda, indirizzo)
