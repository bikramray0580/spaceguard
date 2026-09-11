import { RefreshCw } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import MissionViewport from '../components/MissionViewport'
import ContextPanel from '../components/ContextPanel'
import FeatureDock from '../components/FeatureDock'
import ViewControls from '../components/ViewControls'
import ThreatPulseCard from '../components/ThreatPulseCard'
import { useMissionContext } from '../layouts/useMissionContext'
import { useOrbitalData } from '../hooks/useOrbitalData'

export default function DashboardPage() {
  const {
    selectedThreat,
    setSelectedThreat,
    simulation,
    objects,
    threats,
    threatsStatus,
    threatsCompleted,
    threatsAttempted,
    refreshThreats,
  } = useMissionContext()

  const [activePanel, setActivePanel] = useState(null)
  const [selectedObjectId, setSelectedObjectId] = useState(null)

  const orbitalData = useOrbitalData(objects)

  const selectedObject = objects.find(
    (object) => object.id === selectedObjectId,
  ) ?? null

  const selectedOrbit = selectedObjectId
    ? orbitalData.orbitById.get(selectedObjectId) ?? null
    : null

  const inspectThreat = (threat) => {
    if (threat) {
      setSelectedThreat(threat)
    }
    setActivePanel('risk')
  }

  const selectObject = (objectId) => {
    setSelectedObjectId(objectId)
    setActivePanel('track')
  }

  const navigate = useNavigate()

  const handleSimulation = () => {
    if (!selectedThreat) return
    navigate(`/simulation?threat=${encodeURIComponent(selectedThreat.id)}`)
  }

  const orbitStatus = orbitalData.status
  const isOrbitUnavailable = orbitStatus === 'error'
  const isOrbitLoading = orbitStatus === 'loading'
  const retryMissionData = () => {
    if (typeof refreshThreats === 'function') refreshThreats()
  }

  return (
    <section className="dashboard-workspace">
      <div className="dashboard-mission-label" aria-live="polite">
        <div>
          <span className="eyebrow">MISSION VIEW</span>
          <strong>Orbital awareness workspace</strong>
        </div>
        <span className="dashboard-feed-chip" data-state={orbitStatus}>
          <i />
          {isOrbitUnavailable ? 'DATA UNAVAILABLE' : isOrbitLoading ? 'CONNECTING FEED' : orbitStatus === 'connected' ? 'LIVE ORBIT FEED' : 'AWAITING FEED'}
        </span>
      </div>

      {isOrbitUnavailable && (
        <div className="dashboard-data-banner" role="status">
          <div>
            <strong>Orbital data is not connected</strong>
            <span>Earth remains available as a spatial reference. Live objects and conjunctions will appear when the mission feed reconnects.</span>
          </div>
          <button type="button" onClick={retryMissionData}>
            <RefreshCw size={14} />
            Retry connection
          </button>
        </div>
      )}

      <MissionViewport
        selectedThreat={selectedThreat}
        selectedObject={selectedObject}
        selectedObjectId={selectedObjectId}
        onObjectSelect={selectObject}
        simulation={simulation}
        orbitalData={orbitalData}
      />

      <ThreatPulseCard
        threats={threats}
        status={threatsStatus}
        completed={threatsCompleted}
        attempted={threatsAttempted}
        onInspect={inspectThreat}
        onRetry={refreshThreats}
      />

      <ContextPanel
        panel={activePanel}
        selectedThreat={selectedThreat}
        selectedObject={selectedObject}
        selectedOrbit={selectedOrbit}
        onSelectThreat={setSelectedThreat}
        simulation={simulation}
        onRunSimulation={handleSimulation}
        onClose={() => setActivePanel(null)}
        threats={threats}
        threatsStatus={threatsStatus}
        threatsCompleted={threatsCompleted}
        threatsAttempted={threatsAttempted}
        refreshThreats={refreshThreats}
      />

      <FeatureDock
        activePanel={activePanel}
        onSelect={setActivePanel}
      />

      <ViewControls />
    </section>
  )
}
