from associazione_toolkit.pagination import PagedResponse, PageParams
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.exceptions.indirizzo import IndirizzoNotFoundError
from app.exceptions.persona import PersonaHasDependentsError, PersonaNotFoundError
from app.repositories.indirizzo_repository import IndirizzoRepository
from app.repositories.persona_repository import PersonaRepository
from app.schemas.indirizzo import IndirizzoResponse
from app.schemas.persona import PersonaCreate, PersonaResponse, PersonaUpdate
from app.services.persona_service import PersonaService

router = APIRouter(prefix="/persone", tags=["persone"])


def get_service(db: AsyncSession = Depends(get_db)) -> PersonaService:
    return PersonaService(PersonaRepository(db), IndirizzoRepository(db))


@router.get("/", response_model=PagedResponse[PersonaResponse])
async def list_persone(
    params: PageParams = Depends(),
    service: PersonaService = Depends(get_service),
) -> PagedResponse[PersonaResponse]:
    return await service.get_all(params)


@router.get("/{persona_id}", response_model=PersonaResponse)
async def get_persona(
    persona_id: int, service: PersonaService = Depends(get_service)
) -> PersonaResponse:
    try:
        return await service.get_by_id(persona_id)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.post("/", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    data: PersonaCreate, service: PersonaService = Depends(get_service)
) -> PersonaResponse:
    return await service.create(data)


@router.patch("/{persona_id}", response_model=PersonaResponse)
async def update_persona(
    persona_id: int,
    data: PersonaUpdate,
    service: PersonaService = Depends(get_service),
) -> PersonaResponse:
    try:
        return await service.update(persona_id, data)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    persona_id: int, service: PersonaService = Depends(get_service)
) -> None:
    try:
        await service.delete(persona_id)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PersonaHasDependentsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


# ── Indirizzi della persona (relazione molti-a-molti) ────────────────────────
@router.get("/{persona_id}/indirizzi", response_model=list[IndirizzoResponse])
async def list_indirizzi_persona(
    persona_id: int, service: PersonaService = Depends(get_service)
) -> list[IndirizzoResponse]:
    try:
        return await service.get_indirizzi(persona_id)
    except PersonaNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.put(
    "/{persona_id}/indirizzi/{indirizzo_id}",
    response_model=list[IndirizzoResponse],
)
async def add_indirizzo_persona(
    persona_id: int,
    indirizzo_id: int,
    service: PersonaService = Depends(get_service),
) -> list[IndirizzoResponse]:
    try:
        return await service.add_indirizzo(persona_id, indirizzo_id)
    except (PersonaNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.delete(
    "/{persona_id}/indirizzi/{indirizzo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_indirizzo_persona(
    persona_id: int,
    indirizzo_id: int,
    service: PersonaService = Depends(get_service),
) -> None:
    try:
        await service.remove_indirizzo(persona_id, indirizzo_id)
    except (PersonaNotFoundError, IndirizzoNotFoundError) as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
