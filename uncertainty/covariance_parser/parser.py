"""Format-neutral covariance parsing; adapters for CDM may call this later."""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Literal
import numpy as np

from ..covariance import Covariance


def parse_covariance(
    values: Iterable[float] | Iterable[Iterable[float]], *, epoch: datetime,
    reference_frame: str, source: str = "unknown", estimated: bool = False,
    format: Literal["matrix", "flat", "diagonal_variance", "standard_deviation"] | None = None,
) -> Covariance:
    """Build a covariance from a supported generic representation.

    With ``format=None``, a 6x6 array selects ``matrix`` and a 36-value flat
    array selects ``flat``. Diagonal forms require their explicit format.
    """
    data = np.asarray(values, dtype=float)
    kind = format
    if kind is None:
        if data.shape == (6, 6): kind = "matrix"
        elif data.size == 36: kind = "flat"
        else: raise ValueError("cannot infer covariance format; specify format for diagonal input")
    if kind == "matrix": matrix = data
    elif kind == "flat":
        if data.size != 36: raise ValueError("flattened covariance must contain 36 values")
        matrix = data.reshape(6, 6)
    elif kind in ("diagonal_variance", "standard_deviation"):
        if data.size != 6: raise ValueError(f"{kind} input must contain six values")
        diagonal = data.reshape(6)
        if kind == "standard_deviation":
            if np.any(diagonal < 0): raise ValueError("standard deviations must be non-negative")
            diagonal = diagonal ** 2
        matrix = np.diag(diagonal)
    else: raise ValueError(f"unsupported covariance format: {kind}")
    return Covariance(matrix, epoch, reference_frame, source, estimated)
