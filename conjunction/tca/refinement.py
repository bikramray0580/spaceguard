"""Bounded golden-section refinement of squared distance."""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Callable

def golden_section_minimize(objective: Callable[[datetime], float], left: datetime, right: datetime,
                            tolerance_seconds: float) -> datetime:
    if tolerance_seconds <= 0 or right <= left: raise ValueError("invalid TCA refinement interval or tolerance")
    origin, lo, hi = left, 0.0, (right-left).total_seconds()
    ratio = (5 ** .5 - 1) / 2
    x1, x2 = hi-ratio*(hi-lo), lo+ratio*(hi-lo)
    f1, f2 = objective(origin+timedelta(seconds=x1)), objective(origin+timedelta(seconds=x2))
    while hi-lo > tolerance_seconds:
        if f1 <= f2:
            hi, x2, f2 = x2, x1, f1; x1 = hi-ratio*(hi-lo); f1 = objective(origin+timedelta(seconds=x1))
        else:
            lo, x1, f1 = x1, x2, f2; x2 = lo+ratio*(hi-lo); f2 = objective(origin+timedelta(seconds=x2))
    return origin + timedelta(seconds=(lo+hi)/2)
