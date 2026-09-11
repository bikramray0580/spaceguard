# Collision / conjunction detection

`collision_engine` performs lightweight, deterministic conjunction screening on
already propagated state vectors. It consumes `orbit_engine.PropagationResult`
objects through `OrbitalState.from_propagation_result()`; it does not parse TLEs
or run SGP4 itself.

## Input

An `OrbitalState` contains an object ID, timezone-aware timestamp, coordinate
frame, `position_km` (`x`, `y`, `z`), and `velocity_km_s` (`x`, `y`, `z`).
Position is in kilometres and velocity is in kilometres per second. States being
compared must use exactly the same timestamp and coordinate frame. Orbit-engine
output is TEME, so all input states must remain TEME unless every state has first
been converted consistently elsewhere.

## Calculations

For state A and B, relative position is `R_B - R_A` and relative velocity is
`V_B - V_A`. Separation is the Euclidean magnitude of relative position, in km.
The relative-velocity magnitude is expressed in km/s.

`find_closest_approach(states_a, states_b)` scans paired samples at matching,
strictly increasing timestamps and selects the smallest sampled separation. It
returns a JSON-serializable `ConjunctionEvent` with IDs, closest-approach time,
miss distance, relative velocity, risk level, and readable reason.

## Initial project risk levels

| Miss distance | Risk |
| --- | --- |
| `<= 1 km` | HIGH |
| `> 1 km` and `<= 10 km` | MEDIUM |
| `> 10 km` | LOW |

These configurable constants are **initial project demonstration/engineering
thresholds**, not ISRO or operational collision-avoidance thresholds.

## Limitations and future integration

This is a sampled conjunction-analysis engine, **not an operational
collision-avoidance system**. It does not interpolate between samples, assess
uncertainty/covariance, model object size, or issue manoeuvre recommendations.
Later, a scheduler can obtain current TLE/OMM data, propagate matching future
TEME timestamps through `orbit_engine`, convert frames consistently if needed,
then pass the resulting state series to this module.

## Example

```python
from collision_engine import OrbitalState, find_closest_approach

states_a = [OrbitalState.from_propagation_result(item) for item in propagated_a]
states_b = [OrbitalState.from_propagation_result(item) for item in propagated_b]
event = find_closest_approach(states_a, states_b)
print(event.to_dict())
```
