from datetime import date

from pydantic import BaseModel, EmailStr

from app.models.socio import StatoSocio


class SocioBase(BaseModel):
    nome: str
    cognome: str
    email: EmailStr
    telefono: str | None = None
    data_nascita: date | None = None
    strumento: str | None = None


class SocioCreate(SocioBase):
    pass


class SocioUpdate(BaseModel):
    nome: str | None = None
    cognome: str | None = None
    email: EmailStr | None = None
    telefono: str | None = None
    data_nascita: date | None = None
    strumento: str | None = None
    stato: StatoSocio | None = None


class SocioResponse(SocioBase):
    id: int
    stato: StatoSocio

    model_config = {"from_attributes": True}
