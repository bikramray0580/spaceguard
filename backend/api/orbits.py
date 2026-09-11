"""Orbit propagation endpoints."""

from fastapi import APIRouter, HTTPException

from orbit_engine import PropagationError, TLEValidationError

from ..schemas.orbit import OrbitResult, PropagateRequest
from ..services.data_service import ObjectNotFoundError, find_object, list_objects
from ..services.orbit_service import create_time_grid, propagate_object

router = APIRouter(prefix="/api/orbits", tags=["orbits"])


@router.post("/propagate", response_model=list[OrbitResult])
def propagate(request: PropagateRequest) -> list[OrbitResult]:
    try:
        if request.object_id is None:
            objects = list_objects()
        elif isinstance(request.object_id, str):
            objects = [find_object(request.object_id)]
        else:
            objects = [find_object(obj_id) for obj_id in request.object_id]
    except ObjectNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    try:
        timestamps = create_time_grid(request.start, request.end, request.step_minutes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    results = []
    for obj in objects:
        try:
            results.append(propagate_object(obj, timestamps))
        except TLEValidationError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PropagationError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
    return results
