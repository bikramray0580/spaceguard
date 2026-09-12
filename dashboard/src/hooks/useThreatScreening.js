import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { screenCatalogue, toThreatViewModel } from '../services/conjunctionApi'

const DEFAULT_OBJECT_LIMIT = 10
const DEFAULT_STEP_MINUTES = 5
const DEFAULT_WINDOW_MINUTES = 120
const DEFAULT_DISTANCE_THRESHOLD_KM = 20_000

const RISK_ORDER = {
  CRITICAL: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
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
    distanceThresholdKm = DEFAULT_DISTANCE_THRESHOLD_KM,
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

  const pairCount = useMemo(
    () => (candidateObjects.length * Math.max(0, candidateObjects.length - 1)) / 2,
    [candidateObjects],
  )

  const reload = useCallback(() => {
    setStatus((current) => (current === 'loading' ? current : 'idle'))
  }, [])

  useEffect(() => {
    if (candidateObjects.length < 2) {
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
    setAttempted(pairCount)
    setSuccessful(0)

    async function loadThreats() {
      try {
        const response = await screenCatalogue(
          {
            objectIds: candidateObjects.map((object) => object.id),
            start: window.start,
            end: window.end,
            stepMinutes,
            distanceThresholdKm,
            maxObjects: objectLimit,
          },
          { signal: controller.signal },
        )

        if (controller.signal.aborted || runRef.current !== runId) return

        const resolved = (response.assessments || [])
          .map((assessment) => {
            const objectA = objects.find((object) => object.id === assessment.object_a)
            const objectB = objects.find((object) => object.id === assessment.object_b)

            return toThreatViewModel(assessment, {
              objectAName: objectA?.name,
              objectBName: objectB?.name,
            })
          })
          .sort(sortThreats)

        setThreats(resolved)
        setSuccessful(resolved.length)
        setCompleted(pairCount)

        if (!resolved.length) {
          setStatus('connected')
          setError(null)
          return
        }

        setStatus('connected')
        setError(null)
      } catch (requestError) {
        if (requestError?.name === 'AbortError') return
        if (runRef.current !== runId) return

        console.error('Unable to screen catalogue conjunctions:', requestError)
        setThreats([])
        setStatus('error')
        setError(requestError)
      }
    }

    loadThreats()

    return () => controller.abort()
  }, [
    candidateObjects,
    distanceThresholdKm,
    durationMinutes,
    objectLimit,
    objects,
    pairCount,
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
    pairCount,
    screeningWindowMinutes: durationMinutes,
    stepMinutes,
    reload,
  }
}
