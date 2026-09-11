"""Orbit propagation endpoints."""
from fastapi import APIRouter, HTTPException
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
        results = []
        for obj in objects:
            states = propagate_object(obj, timestamps)
            results.append({
                "object_id": obj.object_id,
                "object_name": obj.name,
                "states": [
                    {
                        "timestamp": state["timestamp"],
                        "position": state["position"],
                        "velocity": state["velocity"],
                        "coordinate_frame": state["coordinate_frame"],
                        "position_units": state["position_units"],
                        "velocity_units": state["velocity_units"],
                    }
                    for state in states
                ],
            })
        return results
    except ObjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
