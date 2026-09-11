"""Relative-state covariance construction for a conjunction pair."""
from __future__ import annotations
import numpy as np
from .covariance import Covariance
from .cross_covariance import CrossCovariance


def relative_covariance(covariance_a: Covariance, covariance_b: Covariance,
                        cross_covariance_ab: CrossCovariance | None = None) -> np.ndarray:
    """Compute ``P_A + P_B - P_AB - P_AB.T``.

    Omit ``cross_covariance_ab`` only when the two object errors are treated as
    independent. This function deliberately does not infer a cross term.
    """
    if covariance_a.reference_frame != covariance_b.reference_frame:
        raise ValueError("covariance A and B reference frames must match")
    if covariance_a.epoch != covariance_b.epoch:
        raise ValueError("covariance A and B epochs must match")
    if covariance_a.state_order != covariance_b.state_order:
        raise ValueError("covariance A and B state ordering must match")
    if cross_covariance_ab is not None and not isinstance(cross_covariance_ab, CrossCovariance):
        raise ValueError("cross covariance must use the CrossCovariance contract")
    if cross_covariance_ab is None:
        result = covariance_a.matrix + covariance_b.matrix
    else:
        if cross_covariance_ab.reference_frame != covariance_a.reference_frame:
            raise ValueError("cross covariance reference frame must match object covariances")
        if cross_covariance_ab.epoch != covariance_a.epoch:
            raise ValueError("cross covariance epoch must match object covariances")
        if cross_covariance_ab.state_order != covariance_a.state_order:
            raise ValueError("cross covariance state ordering must match object covariances")
        result = covariance_a.matrix + covariance_b.matrix - cross_covariance_ab.matrix - cross_covariance_ab.matrix.T
    # The relative covariance itself must remain a valid covariance.
    validated = Covariance(result, covariance_a.epoch, covariance_a.reference_frame, "relative covariance")
    return validated.matrix.copy()
