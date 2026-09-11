# SpaceGuard Phase 6 Frontend: No-Mock Cleanup

This revision keeps the existing frontend architecture and removes fabricated/demo data from `src`.

## Changed

- Dashboard no longer runs the mock simulation service. The Simulation panel opens the real Simulation workspace for the selected backend conjunction.
- Alerts are derived only from backend-screened conjunctions. The separate hard-coded alert list and fake event timeline were removed.
- Data Analysis now derives metrics and charts only from `useMissionContext()` backend objects/conjunctions. Empty states are explicit when data is unavailable.
- Intel panel no longer uses hard-coded mission metrics.
- Monitoring console no longer renders a fake timeline.
- Preferences no longer advertises a mock/prototype dataset.
- Removed `src/data/mockMissionData.js`.
- Removed `src/data/mockOrbitalData.js`.
- Removed `src/services/simulationService.js`.

## Integrity rule

No orbital object, conjunction, telemetry value, risk result, or maneuver result is fabricated when the backend is unavailable.

## Verification

The latest production build should be run locally with:

```powershell
npm install
npm run build
```
