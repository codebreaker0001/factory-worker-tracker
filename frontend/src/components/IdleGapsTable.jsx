export default function IdleGapsTable({ gaps }) {
  if (!gaps.length) {
    return <p className="empty-note">No idle gaps over the threshold.</p>
  }

  return (
    <table className="idle-table">
      <thead>
        <tr>
          <th>Start</th>
          <th>End</th>
          <th>Duration</th>
        </tr>
      </thead>
      <tbody>
        {gaps.map((g, i) => (
          <tr key={i}>
            <td>{g.start.toFixed(1)}s</td>
            <td>{g.end.toFixed(1)}s</td>
            <td>{g.duration.toFixed(1)}s</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
