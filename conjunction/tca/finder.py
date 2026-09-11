from __future__ import annotations
from datetime import datetime, timedelta
from math import isfinite
from typing import Callable
from .models import TcaSearchResult
from .refinement import golden_section_minimize
from ..models import TcaQuality

def find_tca(distance_squared: Callable[[datetime], float], residual: Callable[[datetime], float], start: datetime, end: datetime,
             *, samples: int, tolerance_seconds: float) -> TcaSearchResult:
    """Screen then refine the lowest sampled candidate; boundary minima retain endpoint."""
    if samples < 3: raise ValueError("samples must be at least 3")
    step = (end-start).total_seconds()/(samples-1)
    times = [start+timedelta(seconds=i*step) for i in range(samples)]
    values = [distance_squared(t) for t in times]
    if not all(isfinite(value) for value in values): raise ValueError("TCA objective must be finite")
    index = min(range(samples), key=values.__getitem__)
    boundary = index in (0, samples-1)
    left, right = times[max(0,index-1)], times[min(samples-1,index+1)]
    tca = times[index] if boundary else golden_section_minimize(distance_squared, left, right, tolerance_seconds)
    return TcaSearchResult(tca, TcaQuality(samples, left, right, residual(tca), True, boundary))
