import { ArrowRight, Clock3, ShieldAlert, Satellite, Zap } from 'lucide-react'
import { formatTimeUntilTca } from '../services/conjunctionApi'

function formatNumber(value, digits = 1) {
  if (value == null || !Number.isFinite(Number(value))) return 'Unavailable'
  return Number(value).toFixed(digits)
}

function ThreatStatus({ status, completed, attempted }) {
  if (status === 'loading') {
    return (
      <span className="threat-pulse-status" data-state="loading">
        <i />
        SCREENING {completed}/{attempted}
      </span>
    )
  }

  if (status === 'error') {
    return (
      <span className="threat-pulse-status" data-state="error">
        <i />
        THREAT FEED UNAVAILABLE
      </span>
    )
  }

  if (status === 'partial') {
    return (
      <span className="threat-pulse-status" data-state="partial">
        <i />
        PARTIAL THREAT FEED
      </span>
    )
  }

  if (status === 'connected') {
    return (
      <span className="threat-pulse-status" data-state="connected">
        <i />
        REAL THREAT FEED
      </span>
    )
  }

  return (
    <span className="threat-pulse-status" data-state="waiting">
      <i />
      WAITING FOR THREATS
    </span>
  )
}

export default function ThreatPulseCard({
  threats = [],
  status = 'idle',
  completed = 0,
  attempted = 0,
  onInspect = () => {},
}) {
  const topThreat = threats[0] ?? null

  return (
    <aside className="threat-pulse-card" aria-label="Top threat summary">
      <div className="threat-pulse-head">
        <div>
          <span className="eyebrow">PRIORITY MONITOR</span>
          <h2>Top threat</h2>
        </div>
        <ThreatStatus
          status={status}
          completed={completed}
          attempted={attempted}
        />
      </div>

      {topThreat ? (
        <>
          <button
            type="button"
            className="threat-pulse-threat"
            onClick={() => onInspect(topThreat)}
            aria-label={`Inspect ${topThreat.objectAName || topThreat.objectA} and ${topThreat.objectBName || topThreat.objectB}`}
          >
            <div className="threat-pulse-title-row">
              <span className="threat-pulse-risk" data-risk-level={topThreat.riskLevel}>
                <ShieldAlert size={16} />
                {topThreat.riskLevel}
              </span>
              <ArrowRight size={16} />
            </div>

            <strong>
              {topThreat.objectAName || topThreat.objectA} × {topThreat.objectBName || topThreat.objectB}
            </strong>

            <span className="threat-pulse-source">Backend conjunction result</span>
          </button>

          <div className="threat-pulse-metrics">
            <div>
              <Satellite size={14} />
              <span>Miss distance</span>
              <strong>{formatNumber(topThreat.missDistanceKm, 1)} km</strong>
            </div>
            <div>
              <Zap size={14} />
              <span>Relative velocity</span>
              <strong>{formatNumber(topThreat.relativeVelocityKmS, 2)} km/s</strong>
            </div>
            <div>
              <Clock3 size={14} />
              <span>TCA</span>
              <strong>{formatTimeUntilTca(topThreat.tca)}</strong>
            </div>
          </div>
        </>
      ) : (
        <div className="threat-pulse-empty" role="status">
          {status === 'loading' ? (
            <>
              <strong>Screening conjunctions</strong>
              <span>Real orbital objects are being checked by the backend.</span>
            </>
          ) : status === 'error' ? (
            <>
              <strong>Threat feed unavailable</strong>
              <span>Open Risk to retry screening or inspect the backend status.</span>
            </>
          ) : (
            <>
              <strong>No screened threat yet</strong>
              <span>The dashboard will surface the highest-ranked conjunction here.</span>
            </>
          )}
        </div>
      )}

      <button
        type="button"
        className="threat-pulse-link"
        onClick={() => onInspect(topThreat)}
        disabled={!topThreat && status !== 'error'}
      >
        {topThreat ? 'Open threat investigation' : 'Open risk monitor'}
        <ArrowRight size={15} />
      </button>
    </aside>
  )
}
