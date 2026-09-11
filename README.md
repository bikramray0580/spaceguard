# SpaceGuard

Uncertainty-aware conjunction assessment system that combines the best available orbital data, validated propagation, and risk prioritization to turn future close approaches into actionable alerts.

## Project Structure

```text
spaceguard/
├── data_ingestion/
│   ├── spacetrack/
│   ├── celestrak/
│   ├── cdm/
│   ├── parsers/
│   └── normalizer/
├── orbit_propagation/
│   ├── propagators/
│   ├── sgp4/
│   ├── state_propagation/
│   ├── benchmarks/
│   └── tests/
├── uncertainty/
│   ├── covariance/
│   ├── covariance_parser/
│   ├── covariance_propagation/
│   ├── encounter_frame/
│   ├── visualization/
│   └── quality_flags/
├── conjunction/
│   ├── screening/
│   ├── tca/
│   ├── miss_distance/
│   ├── relative_velocity/
│   ├── encounter_plane/
│   ├── collision_probability/
│   └── validation/
├── risk/
│   ├── risk_engine/
│   ├── severity/
│   ├── confidence/
│   ├── risk_trend/
│   ├── alert_rules/
│   ├── recommendations/
│   └── decision_tables/
├── dashboard/
│   ├── components/
│   ├── pages/
│   ├── visualizations/
│   └── assets/
├── integration/
│   ├── pipeline/
│   ├── data_contract/
│   ├── config/
│   └── demo/
└── shared/
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── sample/
    ├── tests/
    ├── notebooks/
    ├── docs/
    └── configs/
```

## Development Modules

- **Data Source & Ingestion:** acquire and normalize orbital/conjunction data and preserve provenance.
- **Orbit Propagation:** propagate future position and velocity using a method appropriate to the orbit representation.
- **Covariance & Uncertainty:** parse and propagate covariance and expose uncertainty/data-quality status.
- **Conjunction Mathematics:** perform screening, TCA search, miss-distance and relative-velocity calculations, encounter-plane analysis, and collision-probability calculations when valid inputs are available.
- **Risk & Actionability:** convert technical outputs into severity, confidence/data-quality labels, trends, alerts, and recommended actions.
- **Dashboard & Integration:** connect modules, provide visualization, and package the end-to-end demo.

## Shared Integration Rule

Every important output should carry source/provenance, timestamp, and quality status. Modules should exchange data using a common object/event schema.

## Important Boundary

A heuristic score must not be presented as Probability of Collision (Pc). When authoritative covariance is unavailable, the system should clearly report the limitation and prediction/data-quality status instead.
