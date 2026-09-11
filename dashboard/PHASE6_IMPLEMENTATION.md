# SpaceGuard AI Phase 6 What-If Maneuver Implementation

## Source of truth
- Frontend baseline: latest tested Phase 6 frontend package supplied for this work.
- Backend contract: `feature/person-6-dashboard` in `https://github.com/bikramray0580/spaceguard`.
- Endpoint: `POST /api/simulation/maneuver`.

## Implemented
- Real What-If maneuver API adapter in `src/services/maneuverApi.js`.
- Real request fields: object A/B, target object, window, step, delta-v, RTN direction, execution time.
- Backend-aware error mapping for 400 / 404 / 422 / 500 / 503 and malformed responses.
- Response-shape validation before showing a projected result.
- Execution time is derived from the selected threat TCA and current screening window rather than a continuously moving clock window.
- Automatic execution-time repair when threat, duration, or TCA changes.
- Visible valid burn window and current TCA context in the configuration panel.
- Mission-control loading state with evaluation stages and progress feedback.
- AbortController support for reset/stop so stale responses cannot overwrite a new run.
- Real before/after result presentation.
- Backend-provided risk change is displayed directly: improved / worsened / unchanged.
- Before/after miss distance, relative velocity, TCA, and risk level.
- Post-maneuver risk explanation when supplied by the backend.
- Before/after ML category and projected probability when supplied.
- Maneuver metadata: target, delta-v, direction.
- Reset and second-run behavior.
- Responsive scrolling for the configuration and result surfaces.
- Reduced-motion handling.
- Existing Simulation rendering architecture preserved.

## Intentionally not implemented
- No fabricated post-maneuver orbital animation.
- No local orbital physics or local risk calculation.
- No new backend endpoint.
- No modifications to Dashboard, Risk, Track, Data Analysis, Alerts, or Settings.

## Verification note
A production Vite build could not be completed in the current execution environment because the supplied node_modules tree does not contain the Vite binary and package installation could not use the network/cache. The source package is therefore prepared for local `npm install && npm run build` verification.
