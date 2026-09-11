import {
  Check,
  ChevronDown,
  Clock3,
  Crosshair,
  Info,
  Pause,
  Play,
  RotateCcw,
  Satellite,
  SlidersHorizontal,
  Sparkles,
  TimerReset,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { MANEUVER_DIRECTIONS, runWhatIfManeuver } from '../services/maneuverApi'
import { useMissionContext } from '../layouts/useMissionContext'
import { useOrbitalData } from '../hooks/useOrbitalData'
import MissionViewport from '../components/MissionViewport'
import '../styles/simulation.css'

const SCENARIOS = [
  {
    id: 'conjunction',
    label: 'Orbital conjunction',
    description: 'Evaluate a hypothetical maneuver against a screened threat.',
  },
]

const SPEEDS = [0.5, 1, 2]
const DEFAULT_DURATION = '1 h'
const DEFAULT_STEP = '1 min'

const DIRECTION_META = {
  PROGRADE: 'Along-track +',
  RETROGRADE: 'Along-track −',
  RADIAL_OUT: 'Radial +',
  RADIAL_IN: 'Radial −',
  NORMAL: 'Normal +',
  ANTI_NORMAL: 'Normal −',
}

const DIRECTION_LABELS = {
  PROGRADE: 'Prograde',
  RETROGRADE: 'Retrograde',
  RADIAL_OUT: 'Radial out',
  RADIAL_IN: 'Radial in',
  NORMAL: 'Normal',
  ANTI_NORMAL: 'Anti-normal',
}

const EVALUATION_STEPS = [
  'Preparing maneuver',
  'Applying ΔV impulse',
  'Propagating modified state',
  'Re-screening conjunction',
  'Assessing projected risk',
]

const DURATION_MINUTES = {
  '30 min': 30,
  '1 h': 60,
  '2 h': 120,
  '6 h': 360,
}

const STEP_MINUTES = {
  '30 sec': 0.5,
  '1 min': 1,
  '5 min': 5,
}

function toLocalDateTimeInput(date) {
  if (!(date instanceof Date) || Number.isNaN(date.getTime())) return ''

  const pad = (value) => String(value).padStart(2, '0')

  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function fromDateTimeInput(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function getDurationMinutes(value) {
  return DURATION_MINUTES[value] ?? DURATION_MINUTES[DEFAULT_DURATION]
}

function getStepMinutes(value) {
  return STEP_MINUTES[value] ?? STEP_MINUTES[DEFAULT_STEP]
}

function buildRequestWindow(tcaDate, durationValue) {
  const durationMinutes = getDurationMinutes(durationValue)
  const durationMs = durationMinutes * 60 * 1000
  const postTcaBufferMs = Math.min(30, Math.max(10, Math.round(durationMinutes * 0.25))) * 60 * 1000
  const now = new Date()

  // Anchor the window to the actual event time instead of continually moving
  // it with the current clock. This prevents a previously valid execution time
  // from becoming invalid while the user is configuring the scenario.
  const startCandidate = new Date(tcaDate.getTime() - durationMs)
  const safetyFloor = new Date(now.getTime() - 5 * 60 * 1000)
  const start = startCandidate > safetyFloor ? startCandidate : safetyFloor
  const end = new Date(tcaDate.getTime() + postTcaBufferMs)

  return { start, end }
}

function getValidExecutionTime(tcaDate, durationValue) {
  const { start, end } = buildRequestWindow(tcaDate, durationValue)
  const latest = new Date(Math.min(tcaDate.getTime() - 60 * 1000, end.getTime() - 60 * 1000))
  const preferred = new Date(tcaDate.getTime() - Math.min(15, Math.max(5, getDurationMinutes(durationValue) / 4)) * 60 * 1000)
  const candidate = preferred > start ? preferred : new Date(start.getTime() + Math.max(30_000, Math.min(5 * 60 * 1000, (latest.getTime() - start.getTime()) / 2)))

  if (candidate >= latest) return latest
  return candidate
}

function formatRiskLabel(value) {
  return String(value || 'UNKNOWN').toUpperCase()
}

function formatMetric(value, suffix = '') {
  if (value === null || value === undefined || value === '') return 'Unavailable'
  const number = Number(value)
  if (!Number.isFinite(number)) return String(value)
  return `${number.toFixed(2)}${suffix}`
}

function formatTca(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unavailable'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function formatTcaUtc(value) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Unavailable'
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'UTC',
  }).format(date)
}

function formatDirection(value) {
  return DIRECTION_LABELS[value] || value || 'Unavailable'
}

function getResultTitle(riskChange) {
  if (!riskChange) return 'Scenario result'
  if (riskChange.improved) return 'Projected risk improves'
  if (riskChange.worsened) return 'Projected risk worsens'
  return 'Projected risk remains unchanged'
}

function getResultTone(riskChange) {
  if (!riskChange) return 'neutral'
  if (riskChange.improved) return 'improved'
  if (riskChange.worsened) return 'worsened'
  return 'unchanged'
}

function getRiskTone(level) {
  const normalized = String(level || '').toLowerCase()
  if (normalized === 'high' || normalized === 'critical') return 'danger'
  if (normalized === 'medium' || normalized === 'moderate') return 'warning'
  if (normalized === 'low') return 'nominal'
  return 'neutral'
}

function getMlLabel(prediction) {
  return prediction?.risk_category || 'Unavailable'
}

export default function SimulationPage() {
  const [searchParams] = useSearchParams()
  const {
    selectedThreat,
    setSelectedThreat,
    simulation,
    setSimulation,
    threats = [],
    threatsStatus,
    objects = [],
  } = useMissionContext()

  const orbitalData = useOrbitalData(objects || [])

  const [scenario, setScenario] = useState('conjunction')
  const [duration, setDuration] = useState(DEFAULT_DURATION)
  const [step, setStep] = useState(DEFAULT_STEP)
  const [speed, setSpeed] = useState(1)
  const [advancedOpen, setAdvancedOpen] = useState(true)
  const [targetObject, setTargetObject] = useState('')
  const [deltaV, setDeltaV] = useState('5')
  const [direction, setDirection] = useState('PROGRADE')
  const [executionTime, setExecutionTime] = useState('')
  const [maneuverError, setManeuverError] = useState(null)
  const [evaluationStep, setEvaluationStep] = useState(0)
  const [evaluationProgress, setEvaluationProgress] = useState(0)
  const abortControllerRef = useRef(null)
  const runIdRef = useRef(0)

  const selectedPair = useMemo(
    () =>
      threats.find((threat) => threat.id === selectedThreat?.id) ??
      selectedThreat ??
      threats[0] ??
      null,
    [selectedThreat, threats],
  )

  const tcaDate = useMemo(() => {
    if (!selectedPair?.tca) return null
    const date = new Date(selectedPair.tca)
    return Number.isNaN(date.getTime()) ? null : date
  }, [selectedPair])

  const targetOptions = useMemo(() => {
    if (!selectedPair) return []

    return [
      {
        id: selectedPair.objectA,
        label: selectedPair.objectAName || selectedPair.objectA,
      },
      {
        id: selectedPair.objectB,
        label: selectedPair.objectBName || selectedPair.objectB,
      },
    ]
  }, [selectedPair])

  const requestWindow = useMemo(
    () => (tcaDate ? buildRequestWindow(tcaDate, duration) : null),
    [tcaDate, duration],
  )

  const executionBounds = useMemo(() => {
    if (!requestWindow || !tcaDate) return null
    const latest = new Date(Math.min(
      tcaDate.getTime() - 60 * 1000,
      requestWindow.end.getTime() - 60 * 1000,
    ))
    return {
      start: requestWindow.start,
      end: latest,
    }
  }, [requestWindow, tcaDate])

  useEffect(() => {
    const requestedThreatId = searchParams.get('threat')
    if (!requestedThreatId || !threats.length) return

    const requestedThreat = threats.find((threat) => threat.id === requestedThreatId)
    if (requestedThreat && requestedThreat.id !== selectedThreat?.id) {
      setSelectedThreat(requestedThreat)
    }
  }, [searchParams, selectedThreat, setSelectedThreat, threats])

  useEffect(() => {
    if (!selectedPair) {
      setTargetObject('')
      setExecutionTime('')
      return
    }

    setTargetObject((current) =>
      current === selectedPair.objectA || current === selectedPair.objectB
        ? current
        : selectedPair.objectA,
    )

    setExecutionTime(
      tcaDate ? toLocalDateTimeInput(getValidExecutionTime(tcaDate, duration)) : '',
    )

    setManeuverError(null)
    setEvaluationStep(0)
    setEvaluationProgress(0)
    setSimulation((current) => ({
      ...current,
      active: false,
      progress: 0,
      result: null,
      error: null,
      stage: 'Ready',
    }))
  }, [duration, selectedPair, setSimulation, tcaDate])

  useEffect(() => {
    if (!tcaDate || !executionTime || !executionBounds) return

    const execution = fromDateTimeInput(executionTime)
    if (!execution) return

    if (
      execution < executionBounds.start ||
      execution >= executionBounds.end ||
      execution >= tcaDate
    ) {
      setExecutionTime(toLocalDateTimeInput(getValidExecutionTime(tcaDate, duration)))
      setManeuverError(null)
    }
  }, [duration, executionBounds, executionTime, tcaDate])

  useEffect(() => {
    if (!simulation?.active) return undefined

    const startedAt = Date.now()
    const totalMs = 3800
    let frame = 0

    const timer = window.setInterval(() => {
      const elapsed = Date.now() - startedAt
      const normalized = Math.min(1, elapsed / totalMs)
      const nextStep = Math.min(
        EVALUATION_STEPS.length - 1,
        Math.floor(normalized * EVALUATION_STEPS.length),
      )
      const nextProgress = Math.min(94, Math.round(normalized * 94))

      frame += 1
      setEvaluationStep(nextStep)
      setEvaluationProgress(nextProgress)
      setSimulation((current) => ({
        ...current,
        progress: nextProgress,
        stage: EVALUATION_STEPS[nextStep],
      }))
    }, 120)

    return () => {
      window.clearInterval(timer)
      if (frame === 0) setEvaluationProgress(0)
    }
  }, [setSimulation, simulation?.active])

  const setPair = (id) => {
    const next = threats.find((threat) => threat.id === id)
    if (!next) return

    setSelectedThreat(next)
    setSimulation({
      active: false,
      progress: 0,
      result: null,
      error: null,
      stage: 'Ready',
    })
    setManeuverError(null)
  }

  const runSimulation = async () => {
    if (simulation?.active || !selectedPair) return

    const execution = fromDateTimeInput(executionTime)
    if (!execution) {
      setManeuverError('Choose a valid maneuver execution time.')
      return
    }

    if (!tcaDate) {
      setManeuverError('The selected threat does not contain a valid TCA.')
      return
    }

    if (!targetObject) {
      setManeuverError('Select the object that will perform the maneuver.')
      return
    }

    const deltaVMS = Number(deltaV)
    if (!Number.isFinite(deltaVMS) || deltaVMS <= 0 || deltaVMS > 1000) {
      setManeuverError('Delta-v must be greater than 0 and no more than 1000 m/s.')
      return
    }

    if (!requestWindow || !executionBounds) {
      setManeuverError('A valid screening window could not be prepared for this threat.')
      return
    }

    if (execution < executionBounds.start || execution >= executionBounds.end) {
      setManeuverError(
        `Execution time must be between ${formatTcaUtc(executionBounds.start)} and ${formatTcaUtc(executionBounds.end)} UTC, and earlier than TCA.`,
      )
      return
    }

    if (execution >= tcaDate) {
      setManeuverError('Execution time must be earlier than the current TCA.')
      return
    }

    const currentRun = ++runIdRef.current
    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    setManeuverError(null)
    setEvaluationStep(0)
    setEvaluationProgress(0)
    setSimulation({
      active: true,
      progress: 0,
      result: null,
      error: null,
      stage: EVALUATION_STEPS[0],
    })

    try {
      const response = await runWhatIfManeuver(
        {
          objectA: selectedPair.objectA,
          objectB: selectedPair.objectB,
          objectId: targetObject,
          start: requestWindow.start.toISOString(),
          end: requestWindow.end.toISOString(),
          stepMinutes: getStepMinutes(step),
          deltaVMS,
          direction,
          executionTime: execution.toISOString(),
        },
        { signal: controller.signal },
      )

      if (controller.signal.aborted || runIdRef.current !== currentRun) return

      setEvaluationStep(EVALUATION_STEPS.length - 1)
      setEvaluationProgress(100)
      setSimulation({
        active: false,
        progress: 100,
        result: response,
        error: null,
        stage: 'Complete',
      })
    } catch (error) {
      if (error?.name === 'AbortError') return
      if (runIdRef.current !== currentRun) return

      console.error('What-If maneuver failed:', error)
      const message = error?.message || 'The maneuver could not be evaluated.'
      setManeuverError(message)
      setSimulation({
        active: false,
        progress: 0,
        result: null,
        error: message,
        stage: 'Error',
      })
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null
      }
    }
  }

  const resetSimulation = () => {
    runIdRef.current += 1
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setSimulation({
      active: false,
      progress: 0,
      result: null,
      error: null,
      stage: 'Ready',
    })
    setEvaluationStep(0)
    setEvaluationProgress(0)
    setManeuverError(null)
    if (tcaDate) {
      setExecutionTime(toLocalDateTimeInput(getValidExecutionTime(tcaDate, duration)))
    }
  }

  const cancelVisualRun = () => {
    runIdRef.current += 1
    abortControllerRef.current?.abort()
    abortControllerRef.current = null
    setSimulation({
      active: false,
      progress: 0,
      result: null,
      error: null,
      stage: 'Ready',
    })
    setEvaluationStep(0)
    setEvaluationProgress(0)
    setManeuverError(null)
  }

  useEffect(() => {
    return () => {
      runIdRef.current += 1
      abortControllerRef.current?.abort()
    }
  }, [])

  const isRunning = Boolean(simulation?.active)
  const isComplete = Boolean(simulation?.result) && !isRunning
  const result = simulation?.result
  const before = result?.before
  const after = result?.after
  const riskChange = result?.risk_change
  const resultTone = getResultTone(riskChange)
  const beforeMl = before?.ml_prediction
  const afterMl = after?.ml_prediction
  const evaluationLabel = EVALUATION_STEPS[evaluationStep] || EVALUATION_STEPS[0]

  return (
    <section className="simulation-page">
      <MissionViewport
        selectedThreat={selectedPair}
        simulation={simulation}
        onObjectSelect={() => {}}
        orbitalData={orbitalData}
      />

      <div className="simulation-vignette" aria-hidden="true" />

      <header className="simulation-heading">
        <span className="eyebrow">WHAT-IF MANEUVER</span>
        <h1>Simulation mode</h1>
        <p>
          Test a hypothetical impulsive maneuver against a real screened conjunction and inspect the projected risk change.
        </p>
      </header>

      <aside className="simulation-config" aria-label="What-if maneuver configuration">
        <div className="simulation-panel-heading">
          <div>
            <span className="eyebrow">CONFIGURATION</span>
            <strong>Maneuver setup</strong>
          </div>

          <span className="simulation-ready-dot">
            <i className={isRunning ? 'running' : isComplete ? 'complete' : ''} />
            {isRunning ? 'RUNNING' : isComplete ? 'COMPLETE' : 'READY'}
          </span>
        </div>

        <div className="simulation-section">
          <span className="simulation-label">SCENARIO</span>

          <div className="simulation-scenario">
            {SCENARIOS.map((item) => (
              <button
                type="button"
                key={item.id}
                className={scenario === item.id ? 'active' : ''}
                onClick={() => setScenario(item.id)}
                disabled={isRunning}
              >
                <span className="simulation-scenario-icon">
                  <Crosshair size={15} />
                </span>

                <span>
                  <strong>{item.label}</strong>
                  <small>{item.description}</small>
                </span>

                {scenario === item.id && <Check size={15} />}
              </button>
            ))}
          </div>
        </div>

        <div className="simulation-section">
          <div className="simulation-label-row">
            <span className="simulation-label">THREAT</span>
            <span className="simulation-muted">Real screened conjunction</span>
          </div>

          <label className="simulation-select">
            <Satellite size={15} />
            <select
              value={selectedPair?.id ?? ''}
              onChange={(event) => setPair(event.target.value)}
              disabled={isRunning || !threats.length}
              aria-label="Select screened conjunction"
            >
              {!threats.length && <option value="">No screened conjunction</option>}
              {threats.map((threat) => (
                <option key={threat.id} value={threat.id}>
                  {threat.objectA} × {threat.objectB}
                </option>
              ))}
            </select>
            <ChevronDown size={15} />
          </label>

          <div className="simulation-object-preview">
            {selectedPair ? (
              <>
                <span>{selectedPair.objectAName || selectedPair.objectA}</span>
                <i>×</i>
                <span>{selectedPair.objectBName || selectedPair.objectB}</span>
              </>
            ) : (
              <span>No screened conjunction selected</span>
            )}
          </div>

          {selectedPair && (
            <div className="simulation-threat-strip">
              <span>
                Risk <strong data-risk-tone={getRiskTone(selectedPair.riskLevel)}>{formatRiskLabel(selectedPair.riskLevel)}</strong>
              </span>
              <span>Miss <strong>{formatMetric(selectedPair.missDistanceKm, ' km')}</strong></span>
              <span>TCA <strong>{formatTca(selectedPair.tca)}</strong></span>
            </div>
          )}

          {!selectedPair && (
            <div className="simulation-data-note" role="status">
              {threatsStatus === 'loading'
                ? 'Waiting for the real conjunction screen to finish.'
                : threatsStatus === 'error'
                  ? 'The conjunction service did not return a usable result.'
                  : 'No screened conjunction is available yet.'}
            </div>
          )}
        </div>

        <div className="simulation-section">
          <span className="simulation-label">MANEUVER</span>

          <label className="simulation-field">
            <span>Target object</span>
            <select
              value={targetObject}
              onChange={(event) => setTargetObject(event.target.value)}
              disabled={isRunning || !targetOptions.length}
            >
              {targetOptions.map((object) => (
                <option key={object.id} value={object.id}>
                  {object.label} · {object.id}
                </option>
              ))}
            </select>
          </label>

          <div className="simulation-parameters">
            <label className="simulation-field">
              <span>ΔV · m/s</span>
              <input
                type="number"
                min="0.1"
                max="1000"
                step="0.1"
                inputMode="decimal"
                value={deltaV}
                onChange={(event) => setDeltaV(event.target.value)}
                disabled={isRunning}
              />
            </label>

            <label className="simulation-field">
              <span>Direction · RTN</span>
              <select
                value={direction}
                onChange={(event) => setDirection(event.target.value)}
                disabled={isRunning}
              >
                {MANEUVER_DIRECTIONS.map((value) => (
                  <option key={value} value={value}>
                    {DIRECTION_LABELS[value]}
                  </option>
                ))}
              </select>
              <small className="simulation-field-help">{DIRECTION_META[direction]}</small>
            </label>
          </div>

          <label className="simulation-field">
            <span>Execution time · UTC</span>
            <input
              type="datetime-local"
              value={executionTime}
              onChange={(event) => {
                setExecutionTime(event.target.value)
                setManeuverError(null)
              }}
              disabled={isRunning || !tcaDate}
            />
          </label>

          {tcaDate && executionBounds && (
            <div className="simulation-time-window">
              <div>
                <span>Valid burn window</span>
                <strong>{formatTcaUtc(executionBounds.start)} → {formatTcaUtc(executionBounds.end)}</strong>
              </div>
              <div>
                <span>Current TCA</span>
                <strong>{formatTcaUtc(tcaDate)}</strong>
              </div>
            </div>
          )}
        </div>

        <div className="simulation-section">
          <span className="simulation-label">SCREENING WINDOW</span>

          <div className="simulation-parameters">
            <label className="simulation-field">
              <span>Duration</span>
              <select
                value={duration}
                onChange={(event) => setDuration(event.target.value)}
                disabled={isRunning}
              >
                <option>30 min</option>
                <option>1 h</option>
                <option>2 h</option>
                <option>6 h</option>
              </select>
            </label>

            <label className="simulation-field">
              <span>Step</span>
              <select
                value={step}
                onChange={(event) => setStep(event.target.value)}
                disabled={isRunning}
              >
                <option>30 sec</option>
                <option>1 min</option>
                <option>5 min</option>
              </select>
            </label>
          </div>
        </div>

        <div className="simulation-advanced">
          <button
            type="button"
            className="simulation-advanced-toggle"
            onClick={() => setAdvancedOpen((open) => !open)}
            aria-expanded={advancedOpen}
          >
            <span>
              <SlidersHorizontal size={14} />
              Maneuver metadata
            </span>
            <ChevronDown size={14} className={advancedOpen ? 'rotated' : ''} />
          </button>

          {advancedOpen && (
            <div className="simulation-advanced-body">
              <div><span>Maneuver frame</span><strong>RTN</strong></div>
              <div><span>State frame</span><strong>TEME</strong></div>
              <div><span>Risk engine</span><strong>Backend pipeline</strong></div>
              <div><span>ML assessment</span><strong>Backend service</strong></div>
            </div>
          )}
        </div>

        {maneuverError && (
          <div className="simulation-error" role="alert">
            <Info size={15} />
            <div>
              <strong>What-If could not run</strong>
              <span>{maneuverError}</span>
            </div>
          </div>
        )}

        <div className="simulation-actions">
          <button
            type="button"
            className="simulation-primary"
            onClick={runSimulation}
            disabled={isRunning || !selectedPair || !targetObject}
          >
            <Play size={15} />
            {isRunning ? 'Evaluating maneuver' : isComplete ? 'Run again' : 'Run what-if'}
          </button>

          <button
            type="button"
            className="simulation-secondary"
            onClick={resetSimulation}
            aria-label="Reset What-If maneuver"
          >
            <RotateCcw size={14} />
          </button>
        </div>

        {isRunning && (
          <button
            type="button"
            className="simulation-stop-link"
            onClick={cancelVisualRun}
          >
            <Pause size={13} />
            Stop request
          </button>
        )}
      </aside>

      <aside className="simulation-status" aria-live="polite">
        <div className="simulation-status-top">
          <span className="eyebrow">MANEUVER STATUS</span>
          <span className={`simulation-state ${isRunning ? 'running' : isComplete ? 'complete' : 'ready'}`}>
            {isRunning ? 'RUNNING' : isComplete ? 'COMPLETE' : 'READY'}
          </span>
        </div>

        <div className="simulation-status-title">
          {selectedPair ? (
            <>
              <strong>{selectedPair.objectAName || selectedPair.objectA}</strong>
              <span>×</span>
              <strong>{selectedPair.objectBName || selectedPair.objectB}</strong>
            </>
          ) : (
            <strong>Waiting for a screened conjunction</strong>
          )}
        </div>

        <div className="simulation-status-meta">
          <span><Clock3 size={13} />{duration}</span>
          <span><TimerReset size={13} />{step}</span>
          <span><Satellite size={13} />{targetObject || 'No target'}</span>
        </div>

        {isRunning && (
          <div className="simulation-progress-block">
            <div className="simulation-progress-row">
              <span>{evaluationLabel}</span>
              <strong>{evaluationProgress}%</strong>
            </div>
            <div className="simulation-progress-track" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={evaluationProgress}>
              <i style={{ width: `${evaluationProgress}%` }} />
            </div>
            <div className="simulation-step-list" aria-label="What-If evaluation stages">
              {EVALUATION_STEPS.map((label, index) => (
                <span key={label} className={index < evaluationStep ? 'done' : index === evaluationStep ? 'current' : ''}>
                  <i />{label}
                </span>
              ))}
            </div>
          </div>
        )}

        {!isRunning && isComplete && riskChange && (
          <div className={`simulation-risk-summary ${resultTone}`}>
            <span>{getResultTitle(riskChange)}</span>
            <strong>{formatRiskLabel(riskChange.before)} → {formatRiskLabel(riskChange.after)}</strong>
            <small>{result?.maneuver?.delta_v_m_s} m/s · {formatDirection(result?.maneuver?.direction)}</small>
          </div>
        )}
      </aside>

      <div className="simulation-bottom-bar">
        <div className="simulation-bottom-copy">
          <Sparkles size={14} />
          <div>
            <span className="eyebrow">WHAT-IF MANEUVER</span>
            <strong>
              {isRunning
                ? evaluationLabel
                : isComplete
                  ? 'Projected outcome returned by the backend'
                  : 'Ready to evaluate a hypothetical maneuver'}
            </strong>
          </div>
        </div>

        <div className="simulation-speed" aria-label="Visualization speed">
          <span>Speed</span>
          {SPEEDS.map((value) => (
            <button
              key={value}
              type="button"
              className={speed === value ? 'active' : ''}
              onClick={() => setSpeed(value)}
              disabled={isRunning}
            >
              {value}×
            </button>
          ))}
        </div>

        <div className="simulation-disclaimer">
          Backend maneuver model · hypothetical decision-support analysis
        </div>
      </div>

      {isComplete && before && after && riskChange && (
        <section className="simulation-complete-card" data-risk-change={resultTone} aria-label="What-If maneuver result">
          <div className="simulation-result-header">
            <div>
              <span className="eyebrow">SCENARIO RESULT</span>
              <h2>{getResultTitle(riskChange)}</h2>
              <p>
                {before.object_a} × {before.object_b} · {result?.maneuver?.delta_v_m_s} m/s {formatDirection(result?.maneuver?.direction)} · {formatTcaUtc(result?.maneuver?.execution_time)}
              </p>
            </div>

            <div className={`simulation-result-direction ${resultTone}`}>
              <span>Risk change</span>
              <strong>{formatRiskLabel(riskChange.before)} → {formatRiskLabel(riskChange.after)}</strong>
            </div>
          </div>

          <div className="simulation-comparison-grid">
            <div className="simulation-comparison-column">
              <span className="simulation-comparison-kicker">CURRENT</span>
              <div className="simulation-comparison-metric"><span>Miss distance</span><strong>{formatMetric(before.miss_distance_km, ' km')}</strong></div>
              <div className="simulation-comparison-metric"><span>Relative velocity</span><strong>{formatMetric(before.relative_velocity_km_s, ' km/s')}</strong></div>
              <div className="simulation-comparison-metric"><span>TCA</span><strong>{formatTcaUtc(before.time_of_closest_approach)}</strong></div>
              <div className="simulation-comparison-metric risk"><span>Risk</span><strong>{formatRiskLabel(before.risk_level)}</strong></div>
            </div>

            <div className="simulation-comparison-divider" aria-hidden="true"><span>AFTER ΔV</span></div>

            <div className="simulation-comparison-column after">
              <span className="simulation-comparison-kicker">PROJECTED</span>
              <div className="simulation-comparison-metric">
                <span>Miss distance</span>
                <strong>{formatMetric(after.miss_distance_km, ' km')}</strong>
                <small>{Number(riskChange.miss_distance_delta_km) >= 0 ? '+' : ''}{Number(riskChange.miss_distance_delta_km).toFixed(2)} km</small>
              </div>
              <div className="simulation-comparison-metric">
                <span>Relative velocity</span>
                <strong>{formatMetric(after.relative_velocity_km_s, ' km/s')}</strong>
                <small>{Number(riskChange.relative_velocity_delta_km_s) >= 0 ? '+' : ''}{Number(riskChange.relative_velocity_delta_km_s).toFixed(3)} km/s</small>
              </div>
              <div className="simulation-comparison-metric"><span>TCA</span><strong>{formatTcaUtc(after.time_of_closest_approach)}</strong></div>
              <div className="simulation-comparison-metric risk"><span>Risk</span><strong>{formatRiskLabel(after.risk_level)}</strong></div>
            </div>
          </div>

          <div className="simulation-result-intel">
            <div className="simulation-result-intel-card">
              <span className="simulation-comparison-kicker">RISK EXPLANATION</span>
              <strong>{after.risk_reason || 'Backend did not provide a post-maneuver risk explanation.'}</strong>
            </div>

            <div className="simulation-result-intel-card">
              <span className="simulation-comparison-kicker">AI / ML</span>
              <div className="simulation-ml-summary">
                <span>Before <strong>{getMlLabel(beforeMl)}</strong></span>
                <span>After <strong>{getMlLabel(afterMl)}</strong></span>
                <span>Probability <strong>{Number.isFinite(Number(afterMl?.risk_probability)) ? `${(Number(afterMl.risk_probability) * 100).toFixed(0)}%` : 'Unavailable'}</strong></span>
              </div>
            </div>

            <div className="simulation-result-intel-card">
              <span className="simulation-comparison-kicker">MANEUVER</span>
              <div className="simulation-ml-summary">
                <span>Target <strong>{result?.maneuver?.object_id || 'Unavailable'}</strong></span>
                <span>ΔV <strong>{result?.maneuver?.delta_v_m_s ?? 'Unavailable'} m/s</strong></span>
                <span>Direction <strong>{formatDirection(result?.maneuver?.direction)}</strong></span>
              </div>
            </div>
          </div>

          <div className="simulation-result-note">
            <Info size={14} />
            <span>
              Hypothetical decision-support result. The backend applies the maneuver in RTN, reports the modified state in TEME, and re-runs the existing risk pipeline.
            </span>
          </div>

          <button
            type="button"
            className="simulation-complete-close"
            onClick={resetSimulation}
            aria-label="Dismiss maneuver result"
          >
            <X size={16} />
          </button>
        </section>
      )}
    </section>
  )
}
