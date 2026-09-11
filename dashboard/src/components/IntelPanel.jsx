import { Activity, Crosshair, Radar, ShieldAlert } from 'lucide-react'

export default function IntelPanel({ selectedThreat, objects = [], threats = [] }) {
  const highRisk = threats.filter((threat) => threat.riskLevel === 'HIGH').length

  return (
    <aside className="intel-panel">
      <div className="panel-title">
        <div>
          <span className="eyebrow">LIVE INTELLIGENCE</span>
          <h2>Risk posture</h2>
        </div>
        <Radar size={19} />
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <span><Activity size={15} /> OBJECTS</span>
          <strong>{objects.length || '—'}</strong>
          <small>{objects.length ? 'from backend catalogue' : 'unavailable'}</small>
        </div>
        <div className="stat-card">
          <span><ShieldAlert size={15} /> EVENTS</span>
          <strong>{threats.length || '—'}</strong>
          <small>{threats.length ? 'screened conjunctions' : 'unavailable'}</small>
        </div>
        <div className="stat-card danger">
          <span><Crosshair size={15} /> HIGH RISK</span>
          <strong>{threats.length ? highRisk : '—'}</strong>
          <small>{threats.length ? 'backend classification' : 'unavailable'}</small>
        </div>
      </div>

      {selectedThreat ? (
        <div className="threat-focus">
          <span className="eyebrow">SELECTED THREAT</span>
          <div className="focus-header">
            <span className={`risk-pill ${selectedThreat.riskLevel.toLowerCase()}`}>
              {selectedThreat.riskLevel}
            </span>
            <span>{selectedThreat.window}</span>
          </div>
          <h3>
            {selectedThreat.objectAName || selectedThreat.objectA}
            <em>×</em>
            {selectedThreat.objectBName || selectedThreat.objectB}
          </h3>
          <div className="focus-metrics">
            <span>MISS DISTANCE <b>{selectedThreat.distance}</b></span>
            <span>REL. VELOCITY <b>{selectedThreat.velocity}</b></span>
          </div>
          <p>{selectedThreat.riskReason}</p>
        </div>
      ) : (
        <div className="context-empty-state">
          No backend-screened conjunction is currently selected.
        </div>
      )}
    </aside>
  )
}
