# SpaceGuard AI — Development Handoff

This document is the permanent development handoff and source of truth for the
repository's current state, product direction, and implementation constraints.
It describes what exists today; it does not imply that planned capabilities are
implemented.

## 1. Project purpose

SpaceGuard AI is an AI-powered space-object collision risk prediction and
monitoring platform.

The repository is currently a Python core prototype. Its implemented scientific
pipeline is:

```text
TLE input
  → SGP4 orbital propagation
  → propagated position/velocity states
  → sampled closest-approach calculation
  → deterministic distance-based risk classification
```

This is not currently an ML prediction system or an operational
collision-avoidance platform.

## 2. Current implementation

### `orbit_engine/`

`orbit_engine` is an implemented Python module for propagating a satellite
Two-Line Element (TLE) set with the `sgp4` package.

- `propagate_tle(name, line1, line2, timestamps)` validates a pair of TLE lines
  and propagates one timestamp or a sequence of timezone-aware timestamps.
- `generate_time_steps(start_time, end_time, step_minutes)` produces an
  inclusive, UTC-normalized timestamp sequence.
- Invalid or mismatched TLEs raise `TLEValidationError`; invalid SGP4 state
  calculations raise `PropagationError`.
- Outputs are `PropagationResult` records with an object ID and name,
  timestamp, position, velocity, and coordinate-frame label.
- The coordinate frame is **TEME** (True Equator, Mean Equinox), as produced
  by SGP4. This module does not convert it to ITRF/ECEF or another frame.
- Position is measured in **kilometres (km)**.
- Velocity is measured in **kilometres per second (km/s)**.
- `PropagationResult.to_dict()` provides a JSON-serializable representation
  with UTC timestamps using a `Z` suffix.
- Tests and a local demonstration script exist.

Conceptual propagation output:

```json
{
  "object_id": "25544",
  "object_name": "ISS (ZARYA)",
  "timestamp": "2024-01-02T12:00:00Z",
  "position": {"x_km": 1234.56, "y_km": 5678.9, "z_km": 2345.67},
  "velocity": {"x_km_s": 1.23, "y_km_s": 6.45, "z_km_s": 2.1},
  "coordinate_frame": "TEME"
}
```

### `collision_engine/`

`collision_engine` is an implemented Python module for deterministic, sampled
conjunction analysis. It does not parse TLEs or propagate orbits itself.

- `OrbitalState.from_propagation_result()` adapts an
  `orbit_engine.PropagationResult` into the collision-engine input model.
- `find_closest_approach(states_a, states_b)` compares two non-empty state
  series at matching, strictly increasing timestamps in the same coordinate
  frame.
- It calculates relative position (`R_B - R_A`), separation distance, and
  relative-velocity magnitude at each sample, then selects the smallest
  **sampled** separation.
- The output is a JSON-serializable `ConjunctionEvent` containing the two
  object IDs, closest-approach time, miss distance, relative velocity, risk
  level, and readable risk reason.
- No interpolation between samples, uncertainty/covariance analysis, object
  size modelling, or manoeuvre recommendations exists.

Current risk classification is deterministic thresholding, based only on miss
distance:

| Miss distance | Risk level |
| --- | --- |
| `<= 1 km` | `HIGH` |
| `> 1 km` and `<= 10 km` | `MEDIUM` |
| `> 10 km` | `LOW` |

These are initial project demonstration/engineering thresholds, not operational
or ISRO collision-avoidance thresholds. This is **not** currently an ML
prediction system.

Conceptual conjunction output:

```json
{
  "object_a": "SAT-001",
  "object_b": "SAT-002",
  "time_of_closest_approach": "2026-08-22T12:15:00Z",
  "miss_distance_km": 0.7,
  "relative_velocity_km_s": 0.02,
  "risk_level": "HIGH",
  "risk_reason": "HIGH because miss distance = 0.700 km and relative velocity = 0.020 km/s"
}
```

### Supporting repository content

- `docs/orbit-propagation.md` and `docs/collision-detection.md` document the
  existing modules, their contracts, coordinate constraints, and limitations.
- `orbit_engine/tests/` and `collision_engine/tests/` contain module-level unit
  tests; `tests/` contains no project-wide tests yet.
- `requirements.txt` currently declares `sgp4>=2.24` only.
- `README.md` currently contains only the project name and one-line purpose.

## 3. Currently empty or unimplemented areas

The following directories are placeholders containing only `.gitkeep` files:

- `ml/`
- `backend/`
- `frontend/`
- `data/`

Consequently, the repository currently has:

- no HTTP API;
- no database;
- no frontend application;
- no ML model;
- no production data-ingestion pipeline;
- no multi-object operational orchestration;
- no authentication, alert delivery, scheduler, or persistent monitoring
  service.

## 4. Intended future architecture

The intended product architecture is:

```text
Frontend
  ↓
Backend / API
  ↓
Application orchestration
  ↓
Orbit Engine + Collision Engine
  ↓
Data / TLE sources
```

The backend must expose the existing scientific functionality through a clean
API designed around its actual Python-engine outputs. The frontend must not
duplicate orbital propagation or collision calculations.

ML will eventually be integrated as a separate prediction/risk-analysis layer
once its requirements, data sources, training approach, and output contract are
defined. No ML capability should be inferred before then.

## 5. Frontend product direction

The frontend is a mission-control application, not a generic SaaS dashboard.
Users should feel they are operating a space-monitoring system. The central
visual experience is an interactive 3D orbital environment.

The eventual frontend includes:

- Dashboard / Overview
- Track Objects
- Risk Monitor
- Alerts
- Data Science
- Preferences
- 3D orbital visualization
- Object and conjunction details
- Risk analytics, a threat/conjunction table, and an event timeline
- System status, live UTC time, and monitoring statistics

### Locked dashboard layout

- **Top bar:** SpaceGuard branding and application name, system status, UTC
  time, notifications, user/profile, and settings.
- **Left navigation rail:**
  - Navigation: Dashboard, Track, Risk, Alert
  - System: Data Science, Preferences
- **Center:** overview/date heading and a large 3D orbital environment with
  Earth, orbital paths, tracked objects, conjunction markers, and selected
  object visualization.
- **Right intelligence panel:** object count, conjunction count, high-risk
  count, monitored/data freshness, current exposure, Critical/High/Moderate/Low
  state, and selected-threat details.
- **Bottom console:** Risk Monitor, a threat/conjunction table, risk analytics,
  and event timeline.

The orbital environment must remain the visual centerpiece. Do not redesign
this as a conventional navbar → hero → cards → footer website.

### Locked visual theme

The approved theme is **Deep Space Cyan + Amber**:

- Near-black navy background and deep blue-black surfaces.
- Cold cyan for primary UI, active information, and selected orbital elements.
- Mint for nominal/healthy state.
- Amber for warning, attention, and elevated risk.
- Red for critical threats.
- Off-white primary text and muted blue-gray secondary information.

Color meaning is fixed: cyan = information/active/selected; mint = nominal;
amber = warning; red = critical. Glow must be restrained and reserved for
selected objects, orbital trajectories, conjunction points, critical alerts,
and active system indicators. The intended style is aerospace mission control,
not cyberpunk gaming UI.

## 6. 3D orbital environment and primary interaction

The 3D orbital environment is a high-priority future frontend feature. It must
eventually support an interactive Earth with a realistic globe and atmospheric
effect, orbit paths, satellite/object and conjunction markers, appropriate
labels, zoom, rotation, selection, orbit highlighting, and risk-based
highlighting.

It must consume real backend data when that data path exists. Mock or demo
orbital data may be used during UI development only when clearly isolated from
the real data layer; fabricated orbital information must never be presented as
real.

The principal linked interaction is:

```text
Click risk event
  → identify its objects
  → focus/highlight them in the orbital view
  → highlight trajectories and conjunction point
  → update right-side threat panel
  → show detailed risk information
```

The UI should behave as one connected operational system, not independent
panels.

## 7. Data-contract rules

Preserve the units and coordinate-frame information from the scientific engines:

- Propagation data: object ID/name, timestamp, `x/y/z` position in km,
  `x/y/z` velocity in km/s, and `coordinate_frame = TEME`.
- Conjunction data: object A, object B, time of closest approach, miss distance
  in km, relative velocity in km/s, risk level, and risk reason.

Do not silently change units or coordinate systems. Any conversion must be
explicit, documented, and applied consistently before comparison or display.

## 8. Development rules

Before modifying an existing module: understand it, preserve its behavior, run
relevant tests, and make the smallest appropriate change. Do not rewrite the
working `orbit_engine` or `collision_engine` merely to suit a frontend.

### Protected scientific-module boundary

`orbit_engine/` and `collision_engine/` are protected work-in-progress modules
under active development by other team members. Do not modify, refactor, or
depend on undocumented behaviour from either module unless explicitly
instructed. Until stable team-owned contracts are provided, frontend and
application-layer work must use a clean mock/data abstraction rather than a
direct dependency on either protected module.

Do not invent ML capabilities, claim unimplemented features exist, or hard-code
representative numbers into production logic. Keep demo/mock data isolated from
real data sources.

The scientific/data team owns orbital calculations, collision calculations,
ML/data work, and integration/backend work. The frontend/dashboard owner builds
against that work rather than duplicating it.

## 9. Development phases

1. Architecture and contracts
2. Backend/API foundation
3. Frontend application shell
4. 3D orbital environment
5. Risk/conjunction integration
6. Alerts and analytics
7. Real data integration
8. Polish, responsiveness, testing, and performance

The approved visual reference is a dark, dense-but-organized mission-control
dashboard: central Earth/orbital visualization, left navigation rail, right
risk-intelligence panel, and bottom monitoring/analytics console. This visual
direction is locked; extend and improve it rather than repeatedly redesigning
it.
