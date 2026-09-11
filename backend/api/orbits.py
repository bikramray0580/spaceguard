"""Orbit propagation endpoints."""
from fastapi import APIRouter, HTTPException
from orbit_propagation.sgp4.propagator import SGP4Propagator
from ..schemas.orbit import OrbitResult, PropagateRequest
from ..services.data_service import ObjectNotFoundError, find_object, list_objects
from ..services.orbit_service import create_time_grid, propagate_object

router = APIRouter(prefix="/api/orbits", tags=["orbits"])


@router.post("/propagate", response_model=list[OrbitResult])
def propagate(request: PropagateRequest):
    try:
        if request.object_id is None:
            objects = list(list_objects())
        elif isinstance(request.object_id, str):
            objects = [find_object(request.object_id)]
        else:
            objects = [find_object(value) for value in request.object_id]
        timestamps = create_time_grid(request.start, request.end, request.step_minutes)
        return [item for obj in objects for item in propagate_object(obj, timestamps)]
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
