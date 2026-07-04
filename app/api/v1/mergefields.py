from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import require_permission
from app.mergefields.registry import list_all_fields
from app.schemas.mergefield import MergeFieldSchema, MergeFieldsResponse

router = APIRouter(prefix="/mergefields", tags=["mergefields"])


@router.get(
    "/",
    response_model=MergeFieldsResponse,
    dependencies=[Depends(require_permission("templates:read"))],
)
async def list_mergefields() -> MergeFieldsResponse:
    return MergeFieldsResponse(
        entita={
            entity_name: [
                MergeFieldSchema(chiave=f.chiave, etichetta=f.etichetta, tipo=f.tipo)
                for f in fields
            ]
            for entity_name, fields in list_all_fields().items()
        }
    )
