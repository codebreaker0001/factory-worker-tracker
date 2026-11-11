export default function StatTile({ label, value, sublabel }) {
  return (
    <div className="stat-tile">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
      {sublabel && <div className="label">{sublabel}</div>}
    </div>
  )
}
