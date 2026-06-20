from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.configurazione_banda_anno import ConfigurazioneBandaAnno
from app.models.lookups import SezioneRendiconto, SottovoceRendiconto, VoceRendiconto
from app.models.voce_contabilita import VoceContabilita
from app.schemas.configurazione_banda_anno import (
    ConfigurazioneBandaAnnoCreate,
    ConfigurazioneBandaAnnoUpdate,
)


def _with_rels():
    return select(ConfigurazioneBandaAnno).options(
        selectinload(ConfigurazioneBandaAnno.voce_contabilita_quote),
        selectinload(ConfigurazioneBandaAnno.chiuso_da_utente),
    )


class ConfigurazioneBandaAnnoRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all(
        self,
        banda_codice: int | None = None,
        anno: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[ConfigurazioneBandaAnno]:
        stmt = _with_rels()
        if banda_codice is not None:
            stmt = stmt.where(ConfigurazioneBandaAnno.banda_codice == banda_codice)
        if anno is not None:
            stmt = stmt.where(ConfigurazioneBandaAnno.anno == anno)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count_all(
        self,
        banda_codice: int | None = None,
        anno: int | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(ConfigurazioneBandaAnno)
        if banda_codice is not None:
            stmt = stmt.where(ConfigurazioneBandaAnno.banda_codice == banda_codice)
        if anno is not None:
            stmt = stmt.where(ConfigurazioneBandaAnno.anno == anno)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def get_by_id(self, cfg_id: int) -> ConfigurazioneBandaAnno | None:
        stmt = _with_rels().where(ConfigurazioneBandaAnno.id == cfg_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_banda_anno(
        self, banda_codice: int, anno: int
    ) -> ConfigurazioneBandaAnno | None:
        stmt = _with_rels().where(
            ConfigurazioneBandaAnno.banda_codice == banda_codice,
            ConfigurazioneBandaAnno.anno == anno,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def exists_by_banda_anno(self, banda_codice: int, anno: int) -> bool:
        stmt = (
            select(func.count())
            .select_from(ConfigurazioneBandaAnno)
            .where(
                ConfigurazioneBandaAnno.banda_codice == banda_codice,
                ConfigurazioneBandaAnno.anno == anno,
            )
        )
        return bool((await self.db.execute(stmt)).scalar_one())

    async def count_voci_contabilita(self, banda_codice: int) -> int:
        stmt = (
            select(func.count())
            .select_from(VoceContabilita)
            .where(VoceContabilita.banda_codice == banda_codice)
        )
        return (await self.db.execute(stmt)).scalar_one()

    async def lookup_sezione_codice(self, descrizione: str) -> int | None:
        stmt = select(SezioneRendiconto.codice).where(
            func.lower(SezioneRendiconto.descrizione) == descrizione.lower()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def lookup_voce_codice(self, descrizione: str) -> int | None:
        stmt = select(VoceRendiconto.codice).where(
            func.lower(VoceRendiconto.descrizione) == descrizione.lower()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def lookup_sottovoce_codice(self, descrizione: str) -> int | None:
        stmt = select(SottovoceRendiconto.codice).where(
            func.lower(SottovoceRendiconto.descrizione) == descrizione.lower()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    def add_voce_no_commit(
        self,
        banda_codice: int,
        voce_contabilita: str,
        sezione_rendiconto_codice: int,
        voce_rendiconto_codice: int,
        sottovoce_rendiconto_codice: int,
    ) -> None:
        self.db.add(
            VoceContabilita(
                banda_codice=banda_codice,
                voce_contabilita=voce_contabilita,
                sezione_rendiconto_codice=sezione_rendiconto_codice,
                voce_rendiconto_codice=voce_rendiconto_codice,
                sottovoce_rendiconto_codice=sottovoce_rendiconto_codice,
            )
        )

    async def create(
        self, data: ConfigurazioneBandaAnnoCreate
    ) -> ConfigurazioneBandaAnno:
        cfg = ConfigurazioneBandaAnno(**data.model_dump())
        self.db.add(cfg)
        await self.db.commit()
        await self.db.refresh(cfg)
        # reload with relationships
        return await self.get_by_id(cfg.id)  # type: ignore[return-value]

    async def update(
        self, cfg: ConfigurazioneBandaAnno, data: ConfigurazioneBandaAnnoUpdate
    ) -> ConfigurazioneBandaAnno:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(cfg, field, value)
        await self.db.commit()
        await self.db.refresh(cfg)
        return await self.get_by_id(cfg.id)  # type: ignore[return-value]

    async def is_anno_chiuso(self, banda_codice: int, anno: int) -> bool:
        stmt = select(ConfigurazioneBandaAnno.chiuso).where(
            ConfigurazioneBandaAnno.banda_codice == banda_codice,
            ConfigurazioneBandaAnno.anno == anno,
        )
        result = await self.db.execute(stmt)
        chiuso = result.scalar_one_or_none()
        return bool(chiuso)

    async def set_chiusura(
        self,
        cfg: ConfigurazioneBandaAnno,
        chiuso: bool,
        data_chiusura: datetime | None,
        chiuso_da_utente_id: int | None,
    ) -> ConfigurazioneBandaAnno:
        cfg.chiuso = chiuso
        cfg.data_chiusura = data_chiusura
        cfg.chiuso_da_utente_id = chiuso_da_utente_id
        await self.db.commit()
        await self.db.refresh(cfg)
        return await self.get_by_id(cfg.id)  # type: ignore[return-value]

    async def delete(self, cfg: ConfigurazioneBandaAnno) -> None:
        await self.db.delete(cfg)
        await self.db.commit()
