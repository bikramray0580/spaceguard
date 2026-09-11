import {
  AlertTriangle,
  Bell,
  Check,
  ChevronRight,
  Clock3,
  Info,
  RefreshCw,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { useMissionContext } from '../layouts/useMissionContext'
import { formatTca, formatTimeUntilTca } from '../services/conjunctionApi'
import '../styles/alerts.css'

const FILTERS = ['ALL', 'HIGH', 'MEDIUM', 'LOW']

function buildAlerts(threats) {
  return threats.map((threat) => ({
    ...threat,
    time: formatTca(threat.tca),
    title: `${threat.riskLevel} conjunction detected`,
    detail: `${threat.objectAName || threat.objectA} / ${threat.objectBName || threat.objectB}`,
    source: 'RISK MONITOR',
  }))
}

export default function AlertsPage() {
  const {
    threats,
    threatsStatus,
    threatsError,
    refreshThreats,
  } = useMissionContext()

  const [filter, setFilter] = useState('ALL')
  const [selectedAlertId, setSelectedAlertId] = useState(null)
  const [acknowledged, setAcknowledged] = useState([])

  const alerts = useMemo(() => buildAlerts(threats), [threats])
  const filteredAlerts = useMemo(() => {
    if (filter === 'ALL') return alerts
    return alerts.filter((alert) => alert.riskLevel === filter)
  }, [alerts, filter])

  const selectedAlert =
    alerts.find((alert) => alert.id === selectedAlertId) ?? null

  const activeCount = alerts.filter(
    (alert) => !acknowledged.includes(alert.id),
  ).length

  const acknowledge = (id) => {
    if (!id) return
    setAcknowledged((current) =>
      current.includes(id) ? current : [...current, id],
    )
  }

  const acknowledgeAll = () => {
    setAcknowledged(alerts.map((alert) => alert.id))
  }

  const handleRetry = () => {
    refreshThreats?.()
  }

  const stateLabel =
    threatsStatus === 'loading'
      ? 'LOADING ALERT FEED'
      : threatsStatus === 'error'
        ? 'ALERT FEED UNAVAILABLE'
        : alerts.length
          ? `${activeCount} ACTIVE ALERTS`
          : 'AWAITING SCREENING'

  return (
    <section className="alerts-page">
      <header className="alerts-header">
        <div>
          <span className="eyebrow">ALERT MANAGEMENT</span>
          <h1>Alert Center</h1>
          <p>
            Review real conjunction events returned by the mission screening service.
          </p>
        </div>

        <div className="alerts-status" data-state={threatsStatus}>
          <Bell size={15} />
          <span>{stateLabel}</span>
        </div>
      </header>

      <section className="alerts-console" aria-label="Alert management console">
        <div className="alerts-toolbar">
          <div className="alert-filters" role="group" aria-label="Filter alerts">
            {FILTERS.map((item) => (
              <button
                key={item}
                type="button"
                className={filter === item ? 'active' : ''}
                onClick={() => setFilter(item)}
              >
                {item}
              </button>
            ))}
          </div>

          <button
            type="button"
            className="ack-all-button"
            onClick={acknowledgeAll}
            disabled={!alerts.length || activeCount === 0}
          >
            <Check size={14} />
            ACKNOWLEDGE ALL
          </button>
        </div>

        {threatsStatus === 'loading' && (
          <div className="alert-state-card loading" role="status">
            <RefreshCw size={18} className="spinning" />
            <div>
              <span className="eyebrow">LIVE SCREENING</span>
              <strong>Loading real alert data</strong>
              <p>Waiting for the conjunction screening service to return results.</p>
            </div>
          </div>
        )}

        {threatsStatus === 'error' && (
          <div className="alert-state-card error" role="alert">
            <AlertTriangle size={18} />
            <div>
              <span className="eyebrow">DATA UNAVAILABLE</span>
              <strong>The alert feed is not connected</strong>
              <p>{threatsError?.message || 'No real conjunction alert data is currently available.'}</p>
            </div>
            <button type="button" onClick={handleRetry}>
              <RefreshCw size={14} />
              Retry feed
            </button>
          </div>
        )}

        {threatsStatus !== 'loading' && threatsStatus !== 'error' && !alerts.length && (
          <div className="alert-state-card empty" role="status">
            <Info size={18} />
            <div>
              <span className="eyebrow">MONITOR READY</span>
              <strong>No conjunction alerts available</strong>
              <p>Alerts appear here when the screening service returns a real conjunction result.</p>
            </div>
            <button type="button" onClick={handleRetry}>
              <RefreshCw size={14} />
              Refresh feed
            </button>
          </div>
        )}

        {filteredAlerts.length > 0 && (
          <div className="alert-queue">
            <div className="alert-queue-header">
              <div>
                <span className="eyebrow">ALERT QUEUE</span>
                <h2>Operational notifications</h2>
              </div>
              <span>{filteredAlerts.length} EVENTS</span>
            </div>

            {filteredAlerts.map((alert) => {
              const isAcknowledged = acknowledged.includes(alert.id)
              const isSelected = selectedAlertId === alert.id

              return (
                <button
                  key={alert.id}
                  type="button"
                  className={`alert-event ${alert.riskLevel.toLowerCase()} ${isSelected ? 'selected' : ''} ${isAcknowledged ? 'acknowledged' : ''}`}
                  onClick={() => setSelectedAlertId(alert.id)}
                >
                  <span className="event-severity">
                    <AlertTriangle size={16} />
                  </span>
                  <span className="event-time">{alert.time}</span>
                  <span className="event-content">
                    <strong>{alert.title}</strong>
                    <small>{alert.detail}</small>
                    <span>{alert.riskReason || 'Backend conjunction result requires operator review.'}</span>
                  </span>
                  <span className="event-source">{alert.source}</span>
                  <span className="event-status">
                    {isAcknowledged ? (
                      <>
                        <Check size={13} /> ACK
                      </>
                    ) : (
                      'NEW'
                    )}
                  </span>
                  <ChevronRight size={16} />
                </button>
              )
            })}
          </div>
        )}
      </section>

      {selectedAlert && (
        <aside className={`selected-alert-bar ${selectedAlert.riskLevel.toLowerCase()}`}>
          <div className="selected-alert-indicator">
            <AlertTriangle size={16} />
          </div>

          <div className="selected-alert-content">
            <span className="eyebrow">SELECTED ALERT</span>
            <strong>{selectedAlert.title}</strong>
            <small>
              {selectedAlert.detail} · {selectedAlert.source}
            </small>
          </div>

          <div className="selected-alert-meta">
            <span>{formatTimeUntilTca(selectedAlert.tca)}</span>
            <span className={`alert-level ${selectedAlert.riskLevel.toLowerCase()}`}>
              {selectedAlert.riskLevel}
            </span>
          </div>

          <button
            type="button"
            className="acknowledge-button"
            disabled={acknowledged.includes(selectedAlert.id)}
            onClick={() => acknowledge(selectedAlert.id)}
          >
            <Check size={14} />
            {acknowledged.includes(selectedAlert.id) ? 'ACKNOWLEDGED' : 'ACKNOWLEDGE'}
          </button>
        </aside>
      )}

      <section className="alerts-timeline">
        <div className="alerts-section-header">
          <div>
            <span className="eyebrow">MISSION ACTIVITY</span>
            <h2>System event timeline</h2>
          </div>
          <Clock3 size={17} />
        </div>

        <div className="alert-state-card empty timeline-empty">
          <Clock3 size={18} />
          <div>
            <span className="eyebrow">NOT EXPOSED BY API</span>
            <strong>Event history is unavailable</strong>
            <p>The current mission API exposes conjunction results, but not a separate historical event stream.</p>
          </div>
        </div>
      </section>
    </section>
  )
}
