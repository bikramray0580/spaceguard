import { runWhatIfManeuver } from './maneuverApi'

export { runWhatIfManeuver }

// Kept only for backward compatibility with any older prototype callers.
// The Simulation page now uses the real What-If Maneuver API.
export async function runMockSimulation() {
  throw new Error(
    'Prototype simulation is retired. Use the real What-If Maneuver API instead.',
  )
}
