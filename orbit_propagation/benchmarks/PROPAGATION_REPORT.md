# Orbit Propagation Report

## 1. Purpose

The `orbit_propagation` module generates future position and velocity for an object from a source-appropriate orbit representation. Person 2 currently implements TLE/GP propagation with SGP4 over a single epoch or a time window.

This is an engineering foundation for later conjunction and risk work. It is not an operational catalog, and it does not estimate Probability of Collision.

## 2. Supported orbit representation

Currently implemented:

- Two-line element sets (TLE / GP mean elements)

Not implemented in this module:

- osculating Cartesian ephemerides
- numerical integrators
- covariance / uncertainty (Person 3)
- conjunction geometry (Person 4)
- collision probability / risk (Person 5)

## 3. Propagation method

The concrete propagator is `SGP4Propagator` in `orbit_propagation/sgp4/propagator.py`.

- Package: trusted Python `sgp4` (`Satrec.twoline2rv` and `Satrec.sgp4`)
- Algorithm: SGP4/SDP4 as selected by the library from the TLE mean motion
- Frame of the SGP4 result: TEME
- Position units: km
- Velocity units: km/s

`propagate_window()` does not reimplement SGP4. It builds a timestamp sequence and calls `propagate()` for each epoch.

## 4. Input data

| Input | Description |
| --- | --- |
| `line1` | TLE line 1 (string) |
| `line2` | TLE line 2 (string) |
| `timestamp` | single requested epoch (`datetime`) |
| `start_time`, `end_time` | window bounds (`datetime`) |
| `step_seconds` | positive step between states |

Naive datetimes are treated as UTC. Aware datetimes are converted to UTC.

Tests and the benchmark use a fixed ISS TLE (NORAD 25544, epoch 2019-12-09). No network fetch is used.

## 5. Output data

Each sample is a `PropagatedState`:

- `timestamp` — UTC epoch of the sample
- `position` — `(x, y, z)`
- `velocity` — `(vx, vy, vz)`
- `frame` — `TEME`
- `position_units` — `km`
- `velocity_units` — `km/s`

A time window returns a chronological `list[PropagatedState]`.

## 6. Time-window behavior

`propagate_window(line1, line2, start_time, end_time, step_seconds)`:

1. Validates that start/end are datetimes and normalizes them to UTC.
2. Requires `end_time >= start_time`.
3. Requires `step_seconds > 0`.
4. Starts at `start_time`.
5. Advances by `step_seconds`.
6. Includes `end_time` only when a generated timestamp lands on it exactly.
7. Does not step past `end_time`.
8. If `start_time == end_time`, returns one state.

## 7. Validation / test coverage

Unit tests live in `orbit_propagation/tests/` and use the same local TLE fixture.

Covered properties:

- valid single-state TLE propagation
- valid window output and chronological order
- exact step spacing
- aligned end time included; non-aligned end time not overshot
- `start_time == end_time`
- timezone normalization (naive UTC assumption; offset conversion)
- deterministic repeatability for identical inputs
- output type, TEME frame, km / km/s units
- invalid TLE (garbage, empty, non-string)
- invalid timestamp / window timestamps
- zero, negative, and non-numeric step
- `end_time` earlier than `start_time`
- SGP4 failure mapped to `ValueError` where the library reports an error

Tests assert deterministic structure and error handling. They do not invent expected TEME coordinates or claim catalog-grade accuracy.

## 8. Benchmark methodology

Harness: `orbit_propagation/benchmarks/benchmark_propagation.py`

For several local horizons around the fixed TLE epoch it records:

- requested horizon (seconds)
- step size (seconds)
- number of generated states
- wall-clock runtime
- throughput (states per second)
- whether two identical runs return equal states

No later-orbit or official ephemeris file is present in this repository, so the harness does **not** compute position/velocity residuals.

## 9. Benchmark results

Run locally with:

```
python3 -m orbit_propagation.benchmarks.benchmark_propagation
```

Results are machine-dependent runtime/throughput numbers. They demonstrate that the window propagator executes and is repeatable. They do **not** demonstrate orbital prediction accuracy.

## 10. Scientific / reference-data limitations

There is no trusted reference or later orbit solution in this repository (no official ephemeris, no GPS truth, no independent numerical trajectory).

Therefore:

- prediction-error validation against later orbit solutions remains pending
- no residual time series, RMS plots, or accuracy tables are reported
- runtime benchmarks must not be read as accuracy

SGP4 itself is a mean-element analytic model. Typical TLE/SGP4 error grows with time from epoch and is not quantified here.

## 11. What is and is not demonstrated

Demonstrated:

- TLE parse and SGP4 call through the trusted `sgp4` package
- single-epoch and time-window TEME states
- validation of inputs and time-step rules
- local, reproducible runtime/throughput measurement

Not demonstrated:

- operational-grade accuracy
- covariance or uncertainty
- conjunction miss distance or collision probability
- any heuristic score as Probability of Collision
- source-appropriate propagators other than TLE/GP SGP4

## 12. Future extensibility

Other source types can add sibling modules under `orbit_propagation/` (for example numerical integration of Cartesian states) that still emit `PropagatedState`. `propagate()` / `propagate_window()` on those classes should keep the same output contract: timestamp, TEME-or-documented frame, km, km/s.

Prediction-error validation should be added only when a documented, repository-local reference trajectory is available.
