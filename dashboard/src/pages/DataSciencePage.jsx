import {
  Activity,
  ArrowRight,
  BarChart3,
  Database,
  Gauge,
  Radar,
  ShieldAlert,
  Sparkles,
  Target,
  X,
  Zap,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useMissionContext } from '../layouts/useMissionContext'
import '../styles/datascience.css'

const RISK_ORDER = ['HIGH', 'MEDIUM', 'LOW']
const ANALYSIS_TABS = [
  { id: 'overview', label: 'Overview', icon: Radar },
  { id: 'risk', label: 'Risk', icon: ShieldAlert },
  { id: 'conjunctions', label: 'Conjunctions', icon: Target },
  { id: 'velocity', label: 'Velocity', icon: Zap },
  { id: 'telemetry', label: 'Telemetry', icon: Activity },
]

const RISK_META = {
  HIGH: { label: 'High', tone: 'high' },
  MEDIUM: { label: 'Medium', tone: 'medium' },
  LOW: { label: 'Low', tone: 'low' },
}

const parseNumber = (value) => Number.parseFloat(String(value).replace(/[^0-9.-]/g, '')) || 0
const formatObject = (value = '') => value.toLowerCase().replace(/(^|\s)\S/g, (match) => match.toUpperCase())
const severityLabel = (level) => RISK_META[level]?.label ?? level

export default function DataSciencePage() {
  const { objects = [], objectsStatus = 'idle', threats = [], threatsStatus = 'idle' } = useMissionContext()
  const [activeTab, setActiveTab] = useState('overview')
  const [selectedThreatId, setSelectedThreatId] = useState(null)
  const [showInsights, setShowInsights] = useState(false)
  const searchRef = useRef(null)

  const selectedThreat = useMemo(
    () => threats.find((threat) => threat.id === selectedThreatId) ?? null,
    [selectedThreatId, threats],
  )

  const riskCounts = useMemo(
    () => RISK_ORDER.reduce((counts, level) => {
      counts[level] = threats.filter((threat) => threat.riskLevel === level).length
      return counts
    }, {}),
    [threats],
  )

  const attentionCount = riskCounts.HIGH
  const highestRiskThreat = threats[0] ?? null
  const closestThreat = [...threats].sort((a, b) => a.missDistanceKm - b.missDistanceKm)[0] ?? null
  const fastestThreat = [...threats].sort((a, b) => b.relativeVelocityKmS - a.relativeVelocityKmS)[0] ?? null
  const objectCountLabel = objectsStatus === 'connected' ? objects.length : '—'
  const threatCountLabel = threatsStatus === 'connected' || threatsStatus === 'partial' ? threats.length : '—'

  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === '/' && document.activeElement?.tagName !== 'INPUT') {
        event.preventDefault()
        searchRef.current?.focus()
      }
      if (event.key === 'Escape') {
        setSelectedThreatId(null)
        setShowInsights(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  return (
    <section className="data-science-page">
      <header className="ds-page-header">
        <div className="ds-header-copy">
          <span className="ds-eyebrow">MISSION INTELLIGENCE</span>
          <h1>Data analysis</h1>
          <p>Understand the monitored orbital environment without digging through every metric at once.</p>
        </div>
        <div className="ds-live-status">
          <span className={`ds-live-dot ${objectsStatus === 'connected' ? '' : 'offline'}`} />
          <span>{objectsStatus === 'connected' ? 'BACKEND DATA' : 'DATA UNAVAILABLE'}</span>
          <small>{objectsStatus === 'connected' ? `${objects.length} objects` : 'awaiting API'}</small>
        </div>
      </header>

      <section className="ds-snapshot" aria-label="Dataset snapshot">
        <div className="ds-snapshot-label">
          <span className="ds-eyebrow">DATASET SNAPSHOT</span>
          <strong>Current monitoring posture</strong>
        </div>
        <div className="ds-snapshot-metrics">
          <SnapshotMetric label="Objects monitored" value={objectCountLabel} detail={objectsStatus === 'connected' ? 'backend catalogue' : 'unavailable'} />
          <span className="ds-snapshot-divider" />
          <SnapshotMetric label="Active conjunctions" value={threatCountLabel} detail={threats.length ? 'screened events' : 'unavailable'} />
          <span className="ds-snapshot-divider" />
          <SnapshotMetric label="Need attention" value={threats.length ? attentionCount : '—'} detail={threats.length ? 'high risk' : 'unavailable'} tone="attention" />
        </div>
      </section>

      <section className="ds-insight">
        <div className="ds-insight-icon"><Sparkles size={17} /></div>
        <div className="ds-insight-copy">
          <span className="ds-eyebrow">KEY INSIGHT</span>
          <h2>{threats.length ? 'Attention is concentrated in the backend-screened conjunction set.' : 'Analysis is waiting for connected orbital data.'}</h2>
          <p>{threats.length ? 'Open a conjunction to inspect the supporting risk and timing context.' : 'No values are fabricated when the backend is unavailable.'}</p>
        </div>
        <button type="button" className="ds-insight-action" onClick={() => setShowInsights((current) => !current)} aria-expanded={showInsights}>
          {showInsights ? 'Hide insights' : 'More insights'} <ArrowRight size={14} />
        </button>
      </section>

      {showInsights && threats.length > 0 && (
        <section className="ds-extra-insights" aria-label="Additional insights">
          {closestThreat && <InsightLine icon={<Target size={15} />} title="Closest encounter" value={closestThreat.distance} detail={`${formatObject(closestThreat.objectAName || closestThreat.objectA)} × ${formatObject(closestThreat.objectBName || closestThreat.objectB)}`} />}
          {fastestThreat && <InsightLine icon={<Zap size={15} />} title="Fastest encounter" value={fastestThreat.velocity} detail="relative velocity in current conjunction set" />}
          {highestRiskThreat && <InsightLine icon={<ShieldAlert size={15} />} title="Highest severity" value={highestRiskThreat.riskLevel} detail="backend risk classification" tone={RISK_META[highestRiskThreat.riskLevel]?.tone || ''} />}
        </section>
      )}

      <nav className="ds-analysis-tabs" aria-label="Analysis views">
        {ANALYSIS_TABS.map(({ id, label, icon: Icon }) => (
          <button type="button" key={id} className={activeTab === id ? 'active' : ''} onClick={() => { setActiveTab(id); setSelectedThreatId(null) }} aria-current={activeTab === id ? 'page' : undefined}>
            <Icon size={14} /><span>{label}</span>
          </button>
        ))}
      </nav>

      <main className="ds-analysis-stage">
        {activeTab === 'overview' && <OverviewView threats={threats} riskCounts={riskCounts} onSelectThreat={setSelectedThreatId} objectCount={objects.length} objectsStatus={objectsStatus} />}
        {activeTab === 'risk' && <RiskView threats={threats} riskCounts={riskCounts} onSelectThreat={setSelectedThreatId} />}
        {activeTab === 'conjunctions' && <ConjunctionView threats={threats} onSelectThreat={setSelectedThreatId} />}
        {activeTab === 'velocity' && <VelocityView threats={threats} onSelectThreat={setSelectedThreatId} />}
        {activeTab === 'telemetry' && <TelemetryView />}
      </main>

      {selectedThreat && <ThreatInsightDrawer threat={selectedThreat} onClose={() => setSelectedThreatId(null)} />}
    </section>
  )
}

function SnapshotMetric({ label, value, detail, tone = '' }) {
  return <div className={`ds-snapshot-metric ${tone}`}><span>{label}</span><strong>{value}</strong><small>{detail}</small></div>
}

function InsightLine({ icon, title, value, detail, tone = '' }) {
  return <article className={`ds-insight-line ${tone}`}><span className="ds-insight-line-icon">{icon}</span><div><span>{title}</span><strong>{value}</strong></div><small>{detail}</small></article>
}

function PanelHeading({ eyebrow, title, description, action }) {
  return <header className="ds-panel-heading"><div><span className="ds-eyebrow">{eyebrow}</span><h2>{title}</h2>{description && <p>{description}</p>}</div>{action}</header>
}

function OverviewView({ threats, riskCounts, onSelectThreat, objectCount, objectsStatus }) {
  return <section className="ds-view-shell">
    <div className="ds-primary-grid">
      <article className="ds-analysis-panel ds-primary-panel">
        <PanelHeading eyebrow="SCREENED RISK" title="Conjunction posture" description="Risk distribution is derived only from backend-screened conjunctions." />
        {threats.length ? <RiskDistribution threats={threats} riskCounts={riskCounts} detailed /> : <AnalysisEmptyState title="No screened conjunctions" text="This view will populate from real backend screening results." />}
      </article>
      <article className="ds-analysis-panel ds-focus-panel">
        <PanelHeading eyebrow="KEY PATTERN" title="Where attention is focused" description="A direct view of the current backend conjunction pressure." />
        {threats.length ? <ConcentrationChart threats={threats} /> : <AnalysisEmptyState title="No active pattern" text="A concentration view needs real conjunction results." />}
      </article>
    </div>

    <article className="ds-analysis-panel ds-conjunction-preview">
      <PanelHeading eyebrow="NEXT TO EXPLORE" title="Closest active approaches" description="Select a real backend event to inspect its supporting data." action={<span className="ds-panel-count">{threats.length || '—'} events</span>} />
      {threats.length ? <ThreatPreviewList threats={threats} onSelectThreat={onSelectThreat} /> : <AnalysisEmptyState title={objectsStatus === 'connected' ? 'No backend conjunctions returned' : 'Waiting for connected orbital data'} text={objectsStatus === 'connected' ? `${objectCount} tracked objects are available, but no conjunctions are currently exposed.` : 'The frontend will not invent orbital or risk values.'} />}
    </article>
  </section>
}

function RiskView({ threats, riskCounts, onSelectThreat }) {
  return <section className="ds-view-shell">
    <article className="ds-analysis-panel ds-wide-panel">
      <PanelHeading eyebrow="RISK DISTRIBUTION" title="Screened conjunction risk" description="Counts reflect the current backend screening results." />
      {threats.length ? <RiskDistribution threats={threats} riskCounts={riskCounts} detailed /> : <AnalysisEmptyState title="Risk distribution unavailable" text="Connect the backend screening service to populate this analysis." />}
    </article>
    {threats.length ? <ThreatPreviewList threats={threats} onSelectThreat={onSelectThreat} /> : null}
  </section>
}

function ConjunctionView({ threats, onSelectThreat }) {
  return <section className="ds-view-shell">
    <article className="ds-analysis-panel ds-wide-panel">
      <PanelHeading eyebrow="CONJUNCTIONS" title="Screened approaches" description="Only backend-returned conjunctions are shown." />
      {threats.length ? <ThreatPreviewList threats={threats} onSelectThreat={onSelectThreat} /> : <AnalysisEmptyState title="No conjunctions available" text="No backend conjunction results are currently available." />}
    </article>
  </section>
}

function VelocityView({ threats, onSelectThreat }) {
  const maxVelocity = Math.max(...threats.map((threat) => threat.relativeVelocityKmS), 1)
  const maxDistance = Math.max(...threats.map((threat) => threat.missDistanceKm), 1)

  return <section className="ds-view-shell">
    <article className="ds-analysis-panel ds-wide-panel">
      <PanelHeading eyebrow="VELOCITY ANALYSIS" title="Velocity vs miss distance" description="Plotting only the relative velocity and miss distance returned by the backend." />
      {threats.length ? <div className="ds-scatter-chart" role="img" aria-label="Velocity versus miss distance">
        <div className="ds-scatter-grid" />
        <span className="ds-chart-label ds-chart-y">RELATIVE VELOCITY</span>
        <span className="ds-chart-label ds-chart-x">MISS DISTANCE</span>
        {threats.map((threat) => {
          const x = 14 + (Math.max(threat.missDistanceKm, 0) / maxDistance) * 70
          const y = 16 + (Math.max(threat.relativeVelocityKmS, 0) / maxVelocity) * 66
          return <button type="button" key={threat.id} className={`ds-scatter-point ${threat.riskLevel.toLowerCase()}`} style={{ left: `${x}%`, bottom: `${y}%` }} onClick={() => onSelectThreat(threat.id)} aria-label={`${formatObject(threat.objectAName || threat.objectA)} by ${formatObject(threat.objectBName || threat.objectB)}, ${threat.distance} miss distance, ${threat.velocity} relative velocity`} />
        })}
      </div> : <AnalysisEmptyState title="Velocity analysis unavailable" text="A backend conjunction result is required to plot this relationship." />}
    </article>
  </section>
}

function TelemetryView() {
  return <section className="ds-view-shell"><article className="ds-analysis-panel ds-telemetry-state"><div className="ds-telemetry-icon"><Gauge size={22} /></div><span className="ds-eyebrow">TELEMETRY</span><h2>Telemetry is not exposed by the current API.</h2><p>The frontend keeps this state explicit instead of presenting fabricated operational telemetry.</p><div className="ds-telemetry-note"><Database size={14} /><span>Waiting for a connected telemetry source.</span></div></article></section>
}

function RiskDistribution({ threats, riskCounts, detailed = false }) {
  const levels = detailed ? RISK_ORDER : ['HIGH', 'MEDIUM', 'LOW']
  const total = Math.max(threats.length, 1)
  return <div className={`ds-risk-distribution ${detailed ? 'detailed' : ''}`}>
    <div className="ds-donut-wrap"><div className="ds-donut"><div><strong>{threats.length}</strong><span>EVENTS</span></div></div></div>
    <div className="ds-risk-list">
      {levels.map((level) => {
        const count = riskCounts[level] || 0
        const percentage = ((count / total) * 100).toFixed(1)
        return <div className="ds-risk-row" key={level}><span className={`ds-risk-dot ${level.toLowerCase()}`} /><span className="ds-risk-name">{severityLabel(level)}</span><span className="ds-risk-track"><i className={level.toLowerCase()} style={{ width: `${percentage}%` }} /></span><strong>{count}</strong><small>{percentage}%</small></div>
      })}
    </div>
  </div>
}

function ConcentrationChart({ threats }) {
  const ordered = [...threats].sort((a, b) => a.missDistanceKm - b.missDistanceKm).slice(0, 8)
  const maxDistance = Math.max(...ordered.map((threat) => threat.missDistanceKm), 1)
  const selected = ordered[0]
  return <div className="ds-concentration-chart" role="img" aria-label="Conjunction concentration overview">
    <div className="ds-concentration-grid" />
    <span className="ds-concentration-axis y">HIGHER PRIORITY</span>
    <span className="ds-concentration-axis x">LOWER PRESSURE</span>
    {ordered.map((threat, index) => <span key={threat.id} className={`ds-concentration-point ${threat.riskLevel.toLowerCase()}`} style={{ left: `${18 + index * (64 / Math.max(ordered.length - 1, 1))}%`, bottom: `${18 + (1 - threat.missDistanceKm / maxDistance) * 58}%` }} title={`${threat.objectAName || threat.objectA} × ${threat.objectBName || threat.objectB}`} />)}
    {selected && <div className="ds-concentration-callout"><span className="ds-eyebrow">CLOSEST SCREENED PAIR</span><strong>{formatObject(selected.objectAName || selected.objectA)} × {formatObject(selected.objectBName || selected.objectB)}</strong><small>{selected.distance} · {selected.window}</small></div>}
  </div>
}

function ThreatPreviewList({ threats, onSelectThreat }) {
  const sorted = [...threats].sort((a, b) => a.missDistanceKm - b.missDistanceKm)
  return <div className="ds-threat-preview-list">{sorted.map((threat) => <button type="button" className="ds-threat-preview" key={threat.id} onClick={() => onSelectThreat(threat.id)}><span className={`ds-row-severity ${threat.riskLevel.toLowerCase()}`} /><span className="ds-threat-preview-main"><strong>{formatObject(threat.objectAName || threat.objectA)}<span> × </span>{formatObject(threat.objectBName || threat.objectB)}</strong><small>{threat.window}</small></span><span className={`ds-small-status ${threat.riskLevel.toLowerCase()}`}>{severityLabel(threat.riskLevel)}</span><span className="ds-threat-preview-distance">{threat.distance}</span><ArrowRight size={15} /></button>)}</div>
}

function AnalysisEmptyState({ title, text }) {
  return <div className="ds-telemetry-state"><div className="ds-telemetry-icon"><Database size={22} /></div><span className="ds-eyebrow">DATA UNAVAILABLE</span><h2>{title}</h2><p>{text}</p></div>
}

function ThreatInsightDrawer({ threat, onClose }) {
  return <div className="ds-detail-layer"><button type="button" className="ds-detail-backdrop" aria-label="Close data insight" onClick={onClose} /><aside className="ds-detail-drawer" aria-label="Selected analytical item"><header className="ds-detail-header"><div><span className="ds-eyebrow">SELECTED ANALYSIS</span><p>Conjunction detail</p></div><button type="button" className="ds-detail-close" onClick={onClose} aria-label="Close selected analysis"><X size={18} /></button></header><div className="ds-detail-title"><span className={`ds-detail-icon ${threat.riskLevel.toLowerCase()}`}><BarChart3 size={18} /></span><div><span className={`ds-detail-level ${threat.riskLevel.toLowerCase()}`}>{severityLabel(threat.riskLevel)}</span><h2>{formatObject(threat.objectAName || threat.objectA)}<span> × </span>{formatObject(threat.objectBName || threat.objectB)}</h2><p>Supporting analytical context from the selected backend conjunction.</p></div></div><div className="ds-detail-summary"><div><span>Miss distance</span><strong>{threat.distance}</strong></div><div><span>Relative velocity</span><strong>{threat.velocity}</strong></div><div><span>Time to TCA</span><strong>{threat.window}</strong></div></div><div className="ds-detail-note"><Sparkles size={14} /><p>{threat.riskReason}</p></div><div className="ds-detail-actions"><Link to="/track" className="ds-detail-action primary"><Database size={14} />View object<ArrowRight size={14} /></Link><Link to="/risk" className="ds-detail-action"><ShieldAlert size={14} />View threat<ArrowRight size={14} /></Link><Link to="/" className="ds-detail-action"><Radar size={14} />View dashboard<ArrowRight size={14} /></Link></div></aside></div>
}
