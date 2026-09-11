# What-If Maneuver Backend

Backend-only What-If maneuver capability for SpaceGuard AI.

## Endpoint

`POST /api/simulation/maneuver`

## Request

```json
{
  "object_a": "00900",
  "object_b": "00902",
  "object_id": "00900",
  "start": "2026-09-11T00:00:00Z",
  "end": "2026-09-11T02:00:00Z",
  "step_minutes": 5,
  "delta_v_m_s": 12.5,
  "direction": "PROGRADE",
  "execution_time": "2026-09-11T00:30:00Z"
}
```

### Direction values

- `PROGRADE`
- `RETROGRADE`
- `RADIAL_OUT`
- `RADIAL_IN`
- `NORMAL`
- `ANTI_NORMAL`

The maneuver direction is expressed in the target object's local **RTN** frame at the burn time.

### Timestamp rules

All timestamps must be timezone-aware. The backend normalizes accepted timestamps to UTC.

`execution_time` must be inside the requested screening window and must be earlier than the current pre-maneuver TCA.

## Response

The response contains:

- `before`: the existing real conjunction assessment
- `after`: the re-screened assessment after the hypothetical maneuver
- `maneuver`: maneuver metadata, including separate `state_frame` and `maneuver_frame`
- `risk_change`: deterministic risk comparison plus metric deltas

Example shape:

```json
{
  "status": "complete",
  "maneuver": {
    "object_id": "00900",
    "delta_v_m_s": 12.5,
    "direction": "PROGRADE",
    "execution_time": "2026-09-11T00:30:00Z",
    "state_frame": "TEME",
    "maneuver_frame": "RTN"
  },
  "before": { "...": "..." },
  "after": { "...": "..." },
  "risk_change": {
    "before": "HIGH",
    "after": "LOW",
    "improved": true,
    "worsened": false,
    "unchanged": false,
    "miss_distance_delta_km": 120.5,
    "relative_velocity_delta_km_s": -0.12
  }
}
```

## Physics model

The existing SpaceGuard orbit engine exposes SGP4 TLE propagation rather than arbitrary post-burn state propagation. The maneuver service therefore:

1. Gets the real SGP4 state at the requested burn time.
2. Builds the local RTN basis from that real state.
3. Applies an impulsive delta-v to the velocity vector.
4. Propagates the modified state with a deterministic two-body RK4 integrator.
5. Keeps the non-maneuvered participant on the existing SGP4 path.
6. Re-runs the existing collision/risk pipeline.
7. Re-runs the existing ML assessment.

This is a **What-If decision-support prototype**, not a flight-dynamics-grade operational maneuver propagator. The post-burn trajectory does not recreate a new SGP4-compatible TLE and does not model the full SGP4 perturbation model.

The modified trajectory remains in the TEME state-vector representation used by the existing collision pipeline.

## Validation and errors

- `404`: one of the requested objects is not found
- `400`: malformed timestamps, invalid TLE, or propagation failure
- `422`: maneuver-level validation failure, such as a target outside the pair or a burn at/after the current TCA
- `503`: ML assessment is unavailable

## Integration

The package changes only backend code. `backend/main.py` registers the maneuver router.

No frontend files are changed.
