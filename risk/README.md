# Person 5 — Risk & Actionability

This package converts upstream conjunction outputs into an evidence-backed decision card for the dashboard/integration layer.

## Public API

```python
from risk import RiskInput, assess_risk, assess_upstream_risk

# Direct normalized input remains available.
assessment = assess_risk(RiskInput(
    object_a="A",
    object_b="B",
    miss_distance_km=2.4,
    tca_utc="2026-09-12T00:00:00Z",
    covariance_status="AUTHORITATIVE",
    historical_validation="VALIDATED",
    propagation_quality="VALIDATED",
))

# End-to-end handoff from the real upstream contracts:
assessment = assess_upstream_risk(conjunction_result, uncertainty_assessment)
payload = assessment.to_dict()
```

## Upstream integration

`risk.upstream_adapter` is the explicit boundary between Person 3/4 and Person 5. It accepts the real `ConjunctionResult` and optional `UncertaintyAssessment`, maps their fields into `RiskInput`, preserves provenance and quality evidence, and then runs the existing risk engine.

The adapter deliberately does **not** calculate or invent Pc. The current upstream uncertainty contract reports `pc_authoritative=False`, so Pc remains `UNAVAILABLE` until a recognized, scientifically valid Pc calculator supplies an authoritative result.

## Outputs

- `risk_level`: LOW / MEDIUM / HIGH
- `priority`: 1 (highest) through 4 (monitor)
- `confidence`: evidence/data-quality confidence, **not** collision probability
- `trend`: IMPROVING / STABLE / WORSENING / UNKNOWN
- `alert` and `alert_type`
- `recommended_action`: MONITOR / REASSESS / PRIORITIZE_REVIEW
- `pc`: only retained when the upstream result explicitly marks Pc as `AUTHORITATIVE`
- `pc_status`: preserves AUTHORITATIVE / ESTIMATED / UNAVAILABLE
- `quality_status` and `provenance`
- human-readable `explanation`

## Decision-table boundary

Default miss-distance and Pc cutoffs are **prototype heuristics** and configurable through `RiskThresholds`. They are not operational collision-avoidance limits. A heuristic severity decision must never be displayed as a Probability of Collision.

## Tests

Run:

```bash
python -m unittest discover -s risk/tests -v
```
