import { useEffect, useState } from 'react'
import './App.css'
import BarChart from './components/BarChart'
import IdleGapsTable from './components/IdleGapsTable'
import StatTile from './components/StatTile'
import VideoPanel from './components/VideoPanel'

function formatDuration(totalSeconds) {
  const m = Math.floor(totalSeconds / 60)
  const s = Math.round(totalSeconds % 60)
  return m ? `${m}m ${s}s` : `${s}s`
}

export default function App() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch('/metrics.json')
      .then((r) => {
        if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
        return r.json()
      })
      .then(setMetrics)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="app">
      <header>
        <h1>Packing line — cycle time &amp; throughput</h1>
        <p>YOLOv8-pose + zone-based event detection over a fixed-camera packing station.</p>
      </header>

      <VideoPanel src="/out.mp4" />

      {error && (
        <p className="empty-note">
          Couldn't load data/metrics.json — run <code>python export_metrics.py</code> first. ({error})
        </p>
      )}

      {metrics && (
        <>
          <div className="stat-grid">
            <StatTile label="Cartons filled" value={metrics.total_cartons} />
            <StatTile label="Bottles placed" value={metrics.total_bottles} />
            <StatTile
              label="Avg cycle time"
              value={metrics.cycle_stats ? `${metrics.cycle_stats.mean.toFixed(1)}s` : '—'}
              sublabel={
                metrics.cycle_stats
                  ? `median ${metrics.cycle_stats.median.toFixed(1)}s · p90 ${metrics.cycle_stats.p90.toFixed(1)}s`
                  : null
              }
            />
            <StatTile
              label="Total idle time"
              value={formatDuration(metrics.total_idle_sec)}
              sublabel={`${metrics.idle_gaps.length} gap(s) over 5s`}
            />
          </div>

          <div className="charts-row">
            <div className="panel">
              <h2>Throughput (bottles/min)</h2>
              <BarChart
                data={metrics.throughput_per_minute.map((r) => ({ label: r.minute, value: r.count }))}
                formatLabel={(m) => `min ${m}`}
              />
            </div>

            <div className="panel">
              <h2>Cycle time per carton (sec)</h2>
              <BarChart
                data={metrics.cycles.map((c) => ({ label: c.cycle_id, value: c.duration }))}
                formatLabel={(id) => `carton ${id}`}
                formatValue={(v) => v.toFixed(1)}
                unit="s"
                refLines={metrics.cycle_stats ? [{ value: metrics.cycle_stats.mean, label: 'mean' }] : []}
              />
            </div>
          </div>

          <div className="panel">
            <h2>Idle gaps (&gt; 5s between placements)</h2>
            <IdleGapsTable gaps={metrics.idle_gaps} />
          </div>
        </>
      )}
    </div>
  )
}
