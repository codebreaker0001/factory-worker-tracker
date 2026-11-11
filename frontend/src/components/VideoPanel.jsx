export default function VideoPanel({ src }) {
  return (
    <div className="panel video-panel">
      <h2>Annotated line footage</h2>
      {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
      <video src={src} controls />
    </div>
  )
}
