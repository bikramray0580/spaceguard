"""Space object endpoints."""

from fastapi import APIRouter, HTTPException

from ..schemas.object import ObjectResponse
from ..services.data_service import ObjectNotFoundError, find_object, list_objects

router = APIRouter(prefix="/api/objects", tags=["objects"])


@router.get("", response_model=list[ObjectResponse])
def get_objects() -> list[ObjectResponse]:
    return [ObjectResponse(**obj.to_dict()) for obj in list_objects()]


@router.get("/{object_id}", response_model=ObjectResponse)
def get_object(object_id: str) -> ObjectResponse:
    try:
        obj = find_object(object_id)
    except ObjectNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return ObjectResponse(**obj.to_dict())
