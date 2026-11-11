import { useState } from 'react'

const WIDTH = 600
const HEIGHT = 220
const PAD_LEFT = 8
const PAD_RIGHT = 8
const PAD_TOP = 12
const PAD_BOTTOM = 24
const BAR_GAP = 2

// generic single-series bar chart (magnitude by ordered category): reused for
// both throughput-per-minute and cycle-time-per-carton
export default function BarChart({ data, refLines = [], formatValue = (v) => v, formatLabel = (l) => l, unit = '' }) {
  const [hover, setHover] = useState(null)

  if (!data.length) {
    return <p className="empty-note">No data yet.</p>
  }

  const maxValue = Math.max(...data.map((d) => d.value), ...refLines.map((r) => r.value), 1)
  const plotW = WIDTH - PAD_LEFT - PAD_RIGHT
  const plotH = HEIGHT - PAD_TOP - PAD_BOTTOM
  const barW = plotW / data.length - BAR_GAP
  const yFor = (v) => PAD_TOP + plotH - (v / maxValue) * plotH
  const xFor = (i) => PAD_LEFT + i * (barW + BAR_GAP)

  const labelIndices = [...new Set([0, Math.floor((data.length - 1) / 2), data.length - 1])]

  return (
    <div className="chart-wrap">
      <svg className="bar-chart" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} width="100%" role="img">
        <line
          x1={PAD_LEFT}
          y1={PAD_TOP + plotH}
          x2={WIDTH - PAD_RIGHT}
          y2={PAD_TOP + plotH}
          stroke="var(--baseline)"
          strokeWidth="1"
        />

        {refLines.map((r) => (
          <g key={r.label}>
            <line className="ref-line" x1={PAD_LEFT} x2={WIDTH - PAD_RIGHT} y1={yFor(r.value)} y2={yFor(r.value)} />
            <text className="ref-label" x={WIDTH - PAD_RIGHT} y={yFor(r.value) - 3} textAnchor="end">
              {r.label}
            </text>
          </g>
        ))}

        {data.map((d, i) => (
          <rect
            key={d.label}
            className={`bar${hover === i ? ' active' : ''}`}
            x={xFor(i)}
            y={yFor(d.value)}
            width={Math.max(barW, 1)}
            height={Math.max(PAD_TOP + plotH - yFor(d.value), 0)}
            rx="2"
            onMouseEnter={() => setHover(i)}
            onMouseLeave={() => setHover(null)}
          />
        ))}

        {labelIndices.map((i) => (
          <text key={i} className="axis-label" x={xFor(i) + barW / 2} y={HEIGHT - 6} textAnchor="middle">
            {formatLabel(data[i].label)}
          </text>
        ))}
      </svg>

      {hover !== null && (
        <div
          className="chart-tooltip"
          style={{
            left: `${((xFor(hover) + barW / 2) / WIDTH) * 100}%`,
            top: `${(yFor(data[hover].value) / HEIGHT) * 100}%`,
          }}
        >
          {formatLabel(data[hover].label)}: {formatValue(data[hover].value)}
          {unit}
        </div>
      )}
    </div>
  )
}
