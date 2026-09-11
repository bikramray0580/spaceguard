import { ApiError, apiFetch } from './api'

export const MANEUVER_DIRECTIONS = [
  'PROGRADE',
  'RETROGRADE',
  'RADIAL_OUT',
  'RADIAL_IN',
  'NORMAL',
  'ANTI_NORMAL',
]

function friendlyManeuverError(error) {
  if (!(error instanceof ApiError)) return error

  if (error.status === 404) {
    return new ApiError(
      'The What-If maneuver service is unavailable. Check that the current SpaceGuard backend includes the maneuver API.',
      { status: error.status, endpoint: error.endpoint, details: error.details },
    )
  }

  if (error.status === 400) {
    return new ApiError(
      'The maneuver request was rejected because the timestamps or orbital input could not be evaluated.',
      { status: error.status, endpoint: error.endpoint, details: error.details },
    )
  }

  if (error.status === 422) {
    const detail = typeof error.details?.detail === 'string'
      ? error.details.detail
      : error.message

    return new ApiError(
      detail || 'The maneuver could not be evaluated with the selected target, timing, or parameters.',
      { status: error.status, endpoint: error.endpoint, details: error.details },
    )
  }

  if (error.status === 503) {
    return new ApiError(
      'The maneuver was evaluated, but the backend ML assessment is currently unavailable.',
      { status: error.status, endpoint: error.endpoint, details: error.details },
    )
  }

  if (error.status >= 500) {
    return new ApiError(
      'The backend could not complete the maneuver propagation. Check the backend logs and try again.',
      { status: error.status, endpoint: error.endpoint, details: error.details },
    )
  }

  return error
}

function validateScenarioResponse(response) {
  const hasBefore = response?.before && typeof response.before === 'object'
  const hasAfter = response?.after && typeof response.after === 'object'
  const hasRiskChange = response?.risk_change && typeof response.risk_change === 'object'
  const hasManeuver = response?.maneuver && typeof response.maneuver === 'object'

  if (!hasBefore || !hasAfter || !hasRiskChange || !hasManeuver) {
    throw new ApiError(
      'The maneuver service returned an incomplete scenario result. No projected result was displayed.',
      { status: 502, endpoint: '/api/simulation/maneuver', details: response },
    )
  }

  return response
}

export async function runWhatIfManeuver(
  {
    objectA,
    objectB,
    objectId,
    start,
    end,
    stepMinutes = 5,
    deltaVMS,
    direction,
    executionTime,
  },
  options = {},
) {
  if (!objectA || !objectB || !objectId) {
    throw new Error('A valid conjunction and maneuver target are required.')
  }

  if (objectA === objectB) {
    throw new Error('The conjunction must contain two different objects.')
  }

  if (![objectA, objectB].includes(objectId)) {
    throw new Error('The maneuver target must be one of the screened conjunction participants.')
  }

  if (!start || !end || !executionTime) {
    throw new Error('A complete maneuver time window is required.')
  }

  if (!Number.isFinite(Number(stepMinutes)) || Number(stepMinutes) <= 0 || Number(stepMinutes) > 60) {
    throw new Error('Screening step must be greater than 0 and no more than 60 minutes.')
  }

  if (!Number.isFinite(Number(deltaVMS)) || Number(deltaVMS) <= 0 || Number(deltaVMS) > 1000) {
    throw new Error('Delta-v must be greater than 0 and no more than 1000 m/s.')
  }

  if (!MANEUVER_DIRECTIONS.includes(direction)) {
    throw new Error('Select a supported maneuver direction.')
  }

  try {
    const response = await apiFetch('/api/simulation/maneuver', {
      method: 'POST',
      ...options,
      body: {
        object_a: objectA,
        object_b: objectB,
        object_id: objectId,
        start,
        end,
        step_minutes: Number(stepMinutes),
        delta_v_m_s: Number(deltaVMS),
        direction,
        execution_time: executionTime,
      },
    })

    return validateScenarioResponse(response)
  } catch (error) {
    throw friendlyManeuverError(error)
  }
}
