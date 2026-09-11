import {
  ChevronRight,
  Crosshair,
  Orbit,
  Satellite,
  Search,
  RefreshCw,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { useMissionContext } from '../layouts/useMissionContext'
import '../styles/track.css'

const typeOf = (object) => {
  const identifier = `${object.id} ${object.name}`.toUpperCase()

  if (identifier.includes('DEBRIS')) return 'Debris'
  if (identifier.includes('ROCKET')) return 'Rocket body'
  if (identifier.includes('STARLINK')) return 'Satellite'

  return 'Orbital object'
}

function formatEpoch(epoch) {
  if (!epoch) return 'Unavailable'

  const date = new Date(epoch)

  if (Number.isNaN(date.getTime())) return epoch

  return date.toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone: 'UTC',
  })
}

export default function TrackPage() {
  const {
    objects,
    objectsStatus,
    objectsError,
    refreshObjects,
  } = useMissionContext()

  const [search, setSearch] = useState('')
  const [selected, setSelected] = useState(null)
  const [tab, setTab] = useState('overview')
  const [searchParams] = useSearchParams()

  const filteredObjects = useMemo(() => {
    const query = search.trim().toLowerCase()

    if (!query) return objects

    return objects.filter((object) =>
      `${object.id} ${object.name}`
        .toLowerCase()
        .includes(query),
    )
  }, [objects, search])

  const selectObject = (object) => {
    setSelected(object)
    setTab('overview')
  }

  useEffect(() => {
    const requestedId = searchParams.get('object')
    if (!requestedId || !objects.length) return

    const requestedObject = objects.find((object) => object.id === requestedId)
    if (requestedObject && requestedObject.id !== selected?.id) {
      selectObject(requestedObject)
    }
  }, [objects, searchParams, selected?.id])

  return (
    <section className="registry-page">
      <header className="registry-page-heading">
        <div>
          <h1>Orbital object registry</h1>
          <p>
            Search, inspect, and maintain awareness of the
            active tracking catalogue.
          </p>
        </div>

        <div className="registry-heading-status">
          <span>
            <i
              className={
                objectsStatus === 'connected'
                  ? ''
                  : objectsStatus === 'loading'
                    ? 'loading'
                    : 'offline'
              }
            />
            {objectsStatus === 'connected'
              ? `${objects.length} objects · Live catalogue`
              : objectsStatus === 'loading'
                ? 'Connecting to orbital catalogue'
                : 'Orbital catalogue unavailable'}
          </span>

          {objectsStatus === 'error' && (
            <button
              type="button"
              className="registry-retry"
              onClick={refreshObjects}
            >
              <RefreshCw size={14} />
              Retry
            </button>
          )}
        </div>
      </header>

      <div className={`registry-stage ${selected ? 'has-selection' : ''}`}>
        <section
          className="registry-surface"
          aria-label="Orbital object registry"
        >
          <div className="registry-tools">
            <label>
              <Search size={17} />
              <input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search an orbital object"
              />
            </label>

            <div className="registry-filters" aria-label="Registry scope">
              <button type="button" className="active">
                All objects <b>{objects.length}</b>
              </button>
            </div>
          </div>

          {objectsStatus === 'error' && (
            <div className="registry-system-state" role="alert">
              <div className="registry-state-icon" aria-hidden="true">
                <Satellite size={18} />
              </div>

              <div className="registry-state-copy">
                <span className="registry-state-kicker">DATA UNAVAILABLE</span>
                <strong>Orbital catalogue is not connected</strong>
                <span>
                  This workspace only displays objects returned by the
                  mission backend. No substitute catalogue is shown here.
                </span>

                <small>
                  {objectsError?.message ||
                    'Reconnect the SpaceGuard backend to populate tracked objects.'}
                </small>
              </div>

              <button
                type="button"
                className="registry-inline-retry"
                onClick={refreshObjects}
              >
                <RefreshCw size={14} />
                Retry catalogue
              </button>
            </div>
          )}

          <div className="registry-list">
            <div className="registry-columns">
              <span>Object</span>
              <span>Source</span>
              <span>Epoch</span>
            </div>

            {objectsStatus === 'loading' && (
              <div className="registry-loading">
                Loading orbital objects from the backend…
              </div>
            )}

            {objectsStatus !== 'loading' &&
              !objects.length &&
              objectsStatus !== 'error' && (
                <div className="registry-empty" role="status">
                  <div className="registry-empty-icon" aria-hidden="true">
                    <Satellite size={20} />
                  </div>
                  <span className="registry-state-kicker">CATALOGUE READY</span>
                  <strong>Waiting for orbital objects</strong>
                  <span>
                    The registry will populate from the connected mission
                    data service as soon as objects are available.
                  </span>
                </div>
              )}

            {objectsStatus !== 'loading' &&
              objectsStatus !== 'error' &&
              objects.length > 0 &&
              !filteredObjects.length && (
                <div className="registry-empty registry-empty--search" role="status">
                  <div className="registry-empty-icon" aria-hidden="true">
                    <Search size={18} />
                  </div>
                  <strong>No matching objects</strong>
                  <span>Try a different object name or catalogue identifier.</span>
                </div>
              )}

            {objectsStatus !== 'loading' &&
              objectsStatus !== 'error' &&
              filteredObjects.map((object) => (
                <button
                  key={object.id}
                  type="button"
                  onClick={() => selectObject(object)}
                  className={`registry-row ${
                    selected?.id === object.id
                      ? 'selected'
                      : ''
                  }`}
                >
                  <span className="registry-object">
                    <i />
                    <strong>{object.name}</strong>
                    <small>
                      {object.id} · {typeOf(object)}
                    </small>
                  </span>

                  <span className="registry-source">
                    Backend
                  </span>

                  <span className="registry-seen">
                    {formatEpoch(object.epoch)}
                  </span>

                  <ChevronRight size={16} />
                </button>
              ))}
          </div>
        </section>

        {selected && (
          <>
            <button
              type="button"
              className="detail-backdrop"
              aria-label="Close selected object details"
              onClick={() => setSelected(null)}
            />

            <aside
              className="registry-detail"
              aria-label="Selected object detail"
            >
              <div className="detail-top">
                <span className="detail-symbol">
                  <Satellite size={22} />
                </span>

                <div>
                  <p>Selected object</p>
                  <h2>{selected.name}</h2>
                  <small>
                    {selected.id} · {typeOf(selected)}
                  </small>
                </div>

                <button
                  type="button"
                  className="detail-close"
                  aria-label="Close selected object details"
                  onClick={() => setSelected(null)}
                >
                  <X size={17} />
                </button>
              </div>

              <div className="detail-status">
                <span className="risk-badge unclassified">
                  Risk classification pending
                </span>

                <span className="tracked">
                  <i />
                  Backend tracked
                </span>
              </div>

              <nav
                className="detail-tabs"
                aria-label="Object detail sections"
              >
                <button
                  type="button"
                  className={
                    tab === 'overview' ? 'active' : ''
                  }
                  onClick={() => setTab('overview')}
                >
                  Overview
                </button>

                <button
                  type="button"
                  className={
                    tab === 'orbit' ? 'active' : ''
                  }
                  onClick={() => setTab('orbit')}
                >
                  Orbit
                </button>

                <button
                  type="button"
                  className={
                    tab === 'telemetry' ? 'active' : ''
                  }
                  onClick={() => setTab('telemetry')}
                >
                  Telemetry
                </button>

                <button
                  type="button"
                  className={
                    tab === 'risk' ? 'active' : ''
                  }
                  onClick={() => setTab('risk')}
                >
                  Risk
                </button>
              </nav>

              <div className="detail-body">
                {tab === 'overview' && (
                  <div className="detail-values">
                    <div>
                      <span>Object ID</span>
                      <strong>{selected.id}</strong>
                    </div>

                    <div>
                      <span>Source</span>
                      <strong>Backend catalogue</strong>
                    </div>

                    <div>
                      <span>TLE epoch</span>
                      <strong>{formatEpoch(selected.epoch)}</strong>
                    </div>

                    <div>
                      <span>Tracking state</span>
                      <strong>Available</strong>
                    </div>
                  </div>
                )}

                {tab === 'orbit' && (
                  <div className="detail-orbit">
                    <div className="orbit-visual">
                      <div className="orbit-ring">
                        <Orbit size={26} />
                        <i />
                      </div>
                      <span>
                        Propagated orbit will appear here
                      </span>
                    </div>

                    <p className="detail-message">
                      This object is connected to the real
                      backend catalogue. Orbit propagation is
                      the next data integration step, so no
                      synthetic orbital parameters are shown.
                    </p>
                  </div>
                )}

                {tab === 'telemetry' && (
                  <p className="detail-message">
                    Live telemetry is not currently exposed
                    by the backend. This panel intentionally
                    avoids presenting fabricated downlink data.
                  </p>
                )}

                {tab === 'risk' && (
                  <div className="detail-risk">
                    <p className="detail-message">
                      Risk classification will be populated
                      from conjunction screening once the
                      threat pipeline is connected.
                    </p>
                  </div>
                )}
              </div>

              <Link
                to="/"
                className="detail-action"
              >
                <Crosshair size={16} />
                View on dashboard
              </Link>
            </aside>
          </>
        )}
      </div>
    </section>
  )
}
