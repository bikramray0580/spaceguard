"""What-If maneuver endpoint."""

from fastapi import APIRouter, HTTPException

from orbit_engine import PropagationError, TLEValidationError

from ..schemas.maneuver import ManeuverRequest, ManeuverScenarioResult
from ..services.data_service import ObjectNotFoundError, find_object
from ..services.maneuver_service import ManeuverError, run_maneuver
from ..services.ml_service import MLServiceError

router = APIRouter(
    prefix="/api/simulation",
    tags=["simulation"],
)


@router.post(
    "/maneuver",
    response_model=ManeuverScenarioResult,
)
def maneuver(request: ManeuverRequest) -> ManeuverScenarioResult:
    """Run a hypothetical impulsive maneuver and return before/after risk."""
    try:
        object_a = find_object(request.object_a)
        object_b = find_object(request.object_b)
    except ObjectNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    try:
        result = run_maneuver(object_a, object_b, request)
    except ManeuverError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except (TLEValidationError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except PropagationError as error:
        raise HTTPException(status_code=500, detail=str(error)) from error
    except MLServiceError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    return result
