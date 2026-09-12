import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
  assessmentsToThreatViewModels,
  screenCatalogueConjunctions,
} from '../services/conjunctionApi'

const DEFAULT_OBJECT_LIMIT = 10
const DEFAULT_STEP_MINUTES = 5
const DEFAULT_WINDOW_MINUTES = 120

const RISK_ORDER = {
  HIGH: 0,
  MEDIUM: 1,
  LOW: 2,
}

function createScreeningWindow(durationMinutes = DEFAULT_WINDOW_MINUTES) {
  const start = new Date()
  start.setSeconds(0, 0)
  const end = new Date(start.getTime() + durationMinutes * 60 * 1000)

  return {
    start: start.toISOString(),
    end: end.toISOString(),
  }
}

function buildPairs(objects) {
  const pairs = []

  for (let index = 0; index < objects.length; index += 1) {
    for (let next = index + 1; next < objects.length; next += 1) {
      pairs.push([objects[index], objects[next]])
    }
  }

  return pairs
}

function sortThreats(a, b) {
  const riskDifference =
    (RISK_ORDER[a.riskLevel] ?? 99) - (RISK_ORDER[b.riskLevel] ?? 99)

  if (riskDifference !== 0) return riskDifference

  const distanceDifference = a.missDistanceKm - b.missDistanceKm
  if (Number.isFinite(distanceDifference) && distanceDifference !== 0) {
    return distanceDifference
  }

  return a.tcaDate - b.tcaDate
}

export function useThreatScreening(
  objects,
  {
    objectLimit = DEFAULT_OBJECT_LIMIT,
    durationMinutes = DEFAULT_WINDOW_MINUTES,
    stepMinutes = DEFAULT_STEP_MINUTES,
    refreshKey = 0,
  } = {},
) {
  const [threats, setThreats] = useState([])
  const [status, setStatus] = useState('idle')
  const [error, setError] = useState(null)
  const [completed, setCompleted] = useState(0)
  const [attempted, setAttempted] = useState(0)
  const [successful, setSuccessful] = useState(0)
  const runRef = useRef(0)

  const candidateObjects = useMemo(
    () => objects.slice(0, objectLimit),
    [objects, objectLimit],
  )

  const pairs = useMemo(
    () => buildPairs(candidateObjects),
    [candidateObjects],
  )

  const objectMap = useMemo(
    () => new Map(objects.map((object) => [object.id, object])),
    [objects],
  )

  const reload = useCallback(() => {
    setStatus((current) => (current === 'loading' ? current : 'idle'))
  }, [])

  useEffect(() => {
    if (pairs.length === 0) {
      setThreats([])
      setStatus(objects.length >= 2 ? 'idle' : 'waiting')
      setError(null)
      setCompleted(0)
      setAttempted(0)
      setSuccessful(0)
      return undefined
    }

    const controller = new AbortController()
    const runId = ++runRef.current
    const window = createScreeningWindow(durationMinutes)

    setThreats([])
    setStatus('loading')
    setError(null)
    setCompleted(0)
    setAttempted(1)
    setSuccessful(0)

    async function loadThreats() {
      const payload = await screenCatalogueConjunctions(
        {
          objectIds: candidateObjects.map((object) => object.id),
          start: window.start,
          end: window.end,
          stepMinutes,
          maxObjects: objectLimit,
        },
        { signal: controller.signal },
      )

      if (controller.signal.aborted || runRef.current !== runId) return

      const resolved = assessmentsToThreatViewModels(
        payload?.assessments,
        objectMap,
      ).sort(sortThreats)

      setCompleted(1)
      setThreats(resolved)
      setSuccessful(resolved.length)

      if (!resolved.length) {
        setStatus('connected')
        setError(null)
        return
      }

      setStatus('connected')
      setError(null)
    }

    loadThreats().catch((requestError) => {
      if (requestError?.name === 'AbortError') return
      if (runRef.current !== runId) return

      console.error('Unable to screen conjunctions:', requestError)
      setThreats([])
      setStatus('error')
      setError(requestError)
    })

    return () => controller.abort()
  }, [
    candidateObjects,
    durationMinutes,
    objectLimit,
    objectMap,
    objects.length,
    pairs.length,
    refreshKey,
    stepMinutes,
  ])

  return {
    threats,
    status,
    error,
    completed,
    attempted,
    successful,
    candidateObjects,
    candidateObjectCount: candidateObjects.length,
    pairCount: pairs.length,
    screeningWindowMinutes: durationMinutes,
    stepMinutes,
    reload,
  }
}
