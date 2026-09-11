# SpaceGuard nominal conjunction mathematics

```text
Orbit data → propagation → broad screening → TCA refinement → nominal geometry
                                                              ↓
                                                    ConjunctionResult
                                                              ↓
                                              covariance / uncertainty (external)
                                                              ↓
                                                        encounter Pc (external)
```

The package calculates geometry only. **Miss distance is a nominal geometric quantity and is not Probability of Collision.** It neither creates covariance nor derives Pc from nominal distance.

## Components

- `screening`: thresholded coarse pair screen and candidate brackets.
- `tca`: sampling plus bounded golden-section minimization of `||r_rel||²`.
- `relative_velocity`: `v_rel = v_A - v_B`, speed, and radial closing rate.
- `miss_distance`: `r_rel = r_A-r_B`, its norm, and its direction.
- `encounter_plane`: nominal orthogonal plane basis for future covariance projection.
- `validation`: input/state-pair and result checks.
- `collision_probability`: typed downstream extension point only; it provides `NOT_AVAILABLE_WITHOUT_COVARIANCE`, never fake Pc.

`engine.py` orchestrates these components. Its sole propagation dependency is `StatePropagator.state_at(object_id, when) -> StateVector`.

## Mathematics and numerical policy

At each time, `r_rel = r_A-r_B`, `v_rel = v_A-v_B`, and `d = ||r_rel||`. The engine samples the requested interval, brackets its lowest sample, then applies golden-section minimization in that bracket. At interior TCA it records `dot(r_rel, v_rel)` in km²/s, which should approach zero. A constrained endpoint is retained precisely and marked `boundary_minimum`; it does not claim the interior derivative condition. `closing_rate = -dot(r_rel,v_rel)/||r_rel||` is positive while closing and zero at coincident nominal positions.

Times use a UTC-aware datetime convention; positions are **km** and velocities **km/s**. Frames may be `TEME`, `GCRF`, `ITRF`, or `ECEF`, but both objects must use exactly the same label. No frame conversion is implied or performed.

## Contract for uncertainty/covariance

Pass `ConjunctionResult` (or `to_dict()`) downstream. It contains IDs, TCA, relative position/velocity, miss vector/distance/direction, relative speed/direction, closing rate, frame, and `TcaQuality` (bracket, samples, residual, convergence, boundary flag). The downstream module owns covariance propagation, combined covariance, covariance projection, and scientifically justified Pc.

## Limitations

Screening can miss narrow events between samples; choose its interval and threshold for the trajectory regime. Golden-section refinement assumes the selected bracket is locally unimodal. The package does not transform frames, propagate orbits, model uncertainty, or calculate Pc.
