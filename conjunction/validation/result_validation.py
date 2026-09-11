from __future__ import annotations
from math import isfinite
from ..models import ConjunctionResult

def validate_result(result: ConjunctionResult) -> None:
    if result.miss_distance_km < 0 or result.relative_speed_km_s < 0: raise ValueError("distance and speed must be non-negative")
    if not all(isfinite(x) for x in (result.miss_distance_km, result.relative_speed_km_s, result.closing_rate_km_s, result.tca_quality.residual_km2_s)): raise ValueError("result contains non-finite values")
