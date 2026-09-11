"""Linear covariance propagation without a nominal orbit propagator."""
from __future__ import annotations
from datetime import datetime
import numpy as np
from ..covariance import Covariance


def propagate_covariance(covariance: Covariance, phi: object, process_noise: object | None = None,
                         *, evaluation_epoch: datetime | None = None, source: str | None = None) -> Covariance:
    """Return ``Phi P Phi.T + Q`` after full input and result validation."""
    transition = np.asarray(phi, dtype=float)
    noise = np.zeros((6, 6)) if process_noise is None else np.asarray(process_noise, dtype=float)
    if transition.shape != (6, 6): raise ValueError("Phi must have shape (6, 6)")
    if noise.shape != (6, 6): raise ValueError("Q must have shape (6, 6)")
    if not np.all(np.isfinite(transition)) or not np.all(np.isfinite(noise)):
        raise ValueError("Phi and Q must contain only finite values")
    if not np.allclose(noise, noise.T, rtol=0.0, atol=covariance.symmetry_tolerance):
        raise ValueError("Q must be symmetric")
    if float(np.linalg.eigvalsh((noise + noise.T) / 2.0).min()) < -covariance.psd_tolerance:
        raise ValueError("Q must be positive semi-definite")
    is_identity = np.allclose(transition, np.eye(6), rtol=0.0, atol=covariance.symmetry_tolerance)
    if evaluation_epoch is None and not is_identity:
        raise ValueError("evaluation_epoch is required when Phi represents propagation")
    epoch = covariance.epoch if evaluation_epoch is None else evaluation_epoch
    if epoch.tzinfo is None or epoch.utcoffset() is None: raise ValueError("evaluation_epoch must be timezone-aware")
    duration = (epoch - covariance.epoch).total_seconds()
    if not is_identity and duration == 0.0:
        raise ValueError("propagated covariance requires an evaluation_epoch different from source epoch")
    direction = "forward" if duration > 0 else "backward" if duration < 0 else "same_epoch"
    result = transition @ covariance.matrix @ transition.T + noise
    return Covariance(result, epoch, covariance.reference_frame, source or covariance.source,
                      covariance.estimated, covariance.authoritative, covariance.state_order,
                      "propagated with linear state transition matrix", propagation_duration_seconds=duration,
                      propagation_direction=direction)
