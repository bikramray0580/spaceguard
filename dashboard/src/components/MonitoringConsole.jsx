import {
  ChevronRight,
  Clock3,
  Filter,
  ListFilter,} from 'lucide-react'

export default function MonitoringConsole({
  threats,
  selectedThreat,
  onSelect,
}) {
  return (
    <section className="monitoring-console">
      <div className="console-header">
        <div>
          <span className="eyebrow">RISK MONITOR</span>
          <h2>Upcoming conjunction windows</h2>
        </div>

        <div className="console-actions">
          <button>
            <Filter size={15} />
            ALL LEVELS
          </button>

          <button>
            <ListFilter size={15} />
            SORT: TCA
          </button>
        </div>
      </div>

      <div className="console-body">
        <div className="threat-table">
          <div className="table-heading">
            <span>THREAT / OBJECT PAIR</span>
            <span>TIME TO TCA</span>
            <span>MISS DISTANCE</span>
            <span>RISK</span>
          </div>

          {threats.map((threat) => (
            <button
              key={threat.id}
              type="button"
              onClick={() => onSelect(threat)}
              className={`table-row threat-row ${
                selectedThreat?.id === threat.id ? 'selected' : ''
              }`}
            >
              <span className="object-pair">
                <i className={`severity-dot ${threat.level.toLowerCase()}`} />
                <b>{threat.objectA}</b>
                <span>×</span>
                <b>{threat.objectB}</b>
              </span>

              <span>{threat.window}</span>

              <span>{threat.distance}</span>

              <span>
                <span className={`risk-pill ${threat.level.toLowerCase()}`}>
                  {threat.level}
                </span>
              </span>

              <ChevronRight size={17} />
            </button>
          ))}
        </div>

        <div className="event-timeline">
          <span className="eyebrow">EVENT TIMELINE</span>

          <div className="timeline-empty">
            <Clock3 size={16} />
            <strong>Event history unavailable</strong>
            <small>Only backend-screened conjunction results are shown here. A mission event log is not available from the current API.</small>
          </div>
        </div>
      </div>
    </section>
  )
}