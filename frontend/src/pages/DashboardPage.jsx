import { AlertTriangle, ArrowRight, CheckCircle2, Clock3, Crosshair, Database, Gauge, ShieldAlert, Sparkles } from 'lucide-react'
import '../styles/dashboard.css'

const demoThreat = {
  objectA: 'OBJECT 00900', objectB: 'OBJECT 00902', tca: '11 Sep 2026 · 02:14:32 UTC',
  missDistance: '4.20 km', relativeVelocity: '7.42 km/s', risk: 'HIGH', trend: 'WORSENING',
  action: 'PRIORITIZE REVIEW', confidence: 'MEDIUM', covariance: 'UNAVAILABLE', propagation: 'VALIDATED',
  epochAge: 'N/A', pcStatus: 'NOT AUTHORITATIVE', source: 'SpaceGuard conjunction pipeline',
}
function Metric({ label, value, note }) { return <div className="dashboard-metric"><span>{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</div> }
export default function DashboardPage() {
  const threat = demoThreat
  return <main className="dashboard-page">
    <header className="dashboard-header"><div><span className="dashboard-eyebrow">SPACEGUARD · MISSION OVERVIEW</span><h1>Orbital risk dashboard</h1><p>Monitor the screened environment, understand uncertainty, and move directly from evidence to action.</p></div><div className="dashboard-live"><i /> LIVE SCREENING</div></header>
    <section className="dashboard-grid dashboard-hero-grid">
      <article className="dashboard-card threat-card"><div className="card-heading"><div><span className="dashboard-eyebrow">PRIORITY CONJUNCTION</span><h2>{threat.objectA} <em>×</em> {threat.objectB}</h2></div><span className="risk-badge high"><ShieldAlert size={14} /> {threat.risk}</span></div>
        <div className="threat-metrics"><Metric label="TIME OF CLOSE APPROACH" value={threat.tca} /><Metric label="MISS DISTANCE" value={threat.missDistance} /><Metric label="RELATIVE VELOCITY" value={threat.relativeVelocity} /></div>
        <div className="decision-strip"><div><span>RISK TREND</span><strong>{threat.trend}</strong></div><div><span>RECOMMENDED ACTION</span><strong>{threat.action}</strong></div><button type="button">Review evidence <ArrowRight size={15} /></button></div>
      </article>
      <aside className="dashboard-card status-card"><div className="card-heading compact"><div><span className="dashboard-eyebrow">DATA QUALITY</span><h2>Uncertainty posture</h2></div><Gauge size={19} /></div><div className="quality-status"><AlertTriangle size={17} /><strong>{threat.confidence} CONFIDENCE</strong></div><div className="quality-list"><div><span>Covariance</span><b>{threat.covariance}</b></div><div><span>Pc status</span><b>{threat.pcStatus}</b></div><div><span>Propagation</span><b>{threat.propagation}</b></div><div><span>Epoch age</span><b>{threat.epochAge}</b></div></div><p className="quality-note">Collision probability is not shown as an authoritative value because the required covariance inputs are unavailable.</p></aside>
    </section>
    <section className="dashboard-grid dashboard-secondary-grid">
      <article className="dashboard-card evidence-card"><div className="card-heading compact"><div><span className="dashboard-eyebrow">DECISION EVIDENCE</span><h2>Why this event is prioritized</h2></div><Crosshair size={19} /></div><div className="evidence-row"><CheckCircle2 /><div><strong>Close approach is within the prototype HIGH-risk distance threshold.</strong><small>Risk classification is deterministic; it does not represent a probability of collision.</small></div></div><div className="evidence-row"><Clock3 /><div><strong>TCA and screening metrics are attached to the current event.</strong><small>Review source and freshness information before taking operational action.</small></div></div><div className="evidence-row"><Database /><div><strong>Uncertainty data is explicitly qualified.</strong><small>Covariance is unavailable, so Pc remains non-authoritative.</small></div></div></article>
      <article className="dashboard-card intel-card"><div className="card-heading compact"><div><span className="dashboard-eyebrow">PROVENANCE</span><h2>Source & confidence</h2></div><Sparkles size={19} /></div><div className="provenance-block"><span>SOURCE</span><strong>{threat.source}</strong></div><div className="provenance-block"><span>CONFIDENCE</span><strong>{threat.confidence}</strong></div><div className="provenance-block"><span>RISK INTERPRETATION</span><strong>Evidence-backed screening posture</strong></div></article>
    </section>
    <section className="dashboard-card whatif-card"><div className="whatif-copy"><span className="dashboard-eyebrow">WHAT-IF MANEUVER ANALYSIS</span><h2>Explore a hypothetical trajectory change.</h2><p>Apply a maneuver to either participant and compare the real pre-maneuver conjunction against the re-screened scenario.</p></div><div className="whatif-preview"><div><span>BEFORE</span><strong>HIGH</strong><small>4.20 km miss</small></div><ArrowRight size={18} /><div><span>AFTER</span><strong>—</strong><small>Run scenario</small></div><button type="button">Open What-If <ArrowRight size={15} /></button></div></section>
    <footer className="dashboard-footer"><span>Prototype decision-support interface · not an operational collision-avoidance system.</span><span>All timestamps UTC</span></footer>
  </main>
}
