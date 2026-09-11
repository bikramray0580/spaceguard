# Orbit propagation

`orbit_engine` turns a satellite Two-Line Element (TLE) set into a position and
velocity at one or more instants. It uses the Python `sgp4` package, an
implementation of the standard SGP4 orbit model. SGP4 models the orbit described
by a TLE; it is not a collision predictor.

## Inputs

Call `propagate_tle(name, line1, line2, timestamps)` with a display name, the two
TLE lines, and either one timezone-aware `datetime` or an iterable of them.
Datetimes may use any timezone but are normalized to UTC. Naive datetimes are
rejected to avoid an ambiguous propagation instant.

Use `generate_time_steps(start_time, end_time, step_minutes)` for an inclusive
UTC range. The end time must fall exactly on a time step.

## Output and coordinate frame

Each result is a `PropagationResult`. SGP4 returns the state in **TEME** (True
Equator, Mean Equinox) coordinates. Consumers needing ITRF/ECEF or another frame
must perform that conversion explicitly; this module does not relabel TEME data.

- `position.x_km`, `y_km`, and `z_km` are kilometres.
- `velocity.x_km_s`, `y_km_s`, and `z_km_s` are kilometres per second.

For JSON output, call `result.to_dict()`:

```python
{
    "object_id": "25544",
    "object_name": "ISS (ZARYA)",
    "timestamp": "2024-01-02T12:00:00Z",
    "position": {"x_km": 1234.56, "y_km": 5678.90, "z_km": 2345.67},
    "velocity": {"x_km_s": 1.23, "y_km_s": 6.45, "z_km_s": 2.10},
    "coordinate_frame": "TEME"
}
```

## Example

```python
from datetime import datetime, timezone
from orbit_engine import propagate_tle

result = propagate_tle(
    "ISS (ZARYA)",
    "1 25544U 98067A   24001.50000000  .00010000  00000+0  18000-3 0  9999",
    "2 25544  51.6400  25.0000 0005000  60.0000 300.0000 15.50000000    01",
    datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
)
collision_input = result.to_dict()
```

`TLEValidationError` identifies invalid TLE input. `PropagationError` is raised
when SGP4 reports an invalid state, so callers never receive silently invalid
coordinates.
