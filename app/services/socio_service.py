from app.exceptions.socio import SocioDuplicateEmailError, SocioNotFoundError
from app.repositories.socio_repository import SocioRepository
from app.schemas.socio import SocioCreate, SocioResponse, SocioUpdate


class SocioService:
    def __init__(self, repo: SocioRepository) -> None:
        self.repo = repo

    async def get_all(self) -> list[SocioResponse]:
        soci = await self.repo.get_all()
        return [SocioResponse.model_validate(s) for s in soci]

    async def get_by_id(self, socio_id: int) -> SocioResponse:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        return SocioResponse.model_validate(socio)

    async def create(self, data: SocioCreate) -> SocioResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise SocioDuplicateEmailError(data.email)
        socio = await self.repo.create(data)
        return SocioResponse.model_validate(socio)

    async def update(self, socio_id: int, data: SocioUpdate) -> SocioResponse:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        if data.email:
            existing = await self.repo.get_by_email(data.email)
            if existing and existing.id != socio_id:
                raise SocioDuplicateEmailError(data.email)
        updated = await self.repo.update(socio, data)
        return SocioResponse.model_validate(updated)

    async def delete(self, socio_id: int) -> None:
        socio = await self.repo.get_by_id(socio_id)
        if not socio:
            raise SocioNotFoundError(socio_id)
        await self.repo.soft_delete(socio)
