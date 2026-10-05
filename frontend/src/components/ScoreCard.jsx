function scoreColor(score) {
  if (score >= 75) return "#2e7d32"; // green
  if (score >= 50) return "#ed6c02"; // orange
  return "#d32f2f"; // red
}

export default function ScoreCard({ label, score, suffix = "" }) {
  if (score === null || score === undefined) return null;

  return (
    <div className="score-card">
      <div className="score-circle" style={{ borderColor: scoreColor(score) }}>
        <span style={{ color: scoreColor(score) }}>{score}{suffix}</span>
      </div>
      <p>{label}</p>
    </div>
  );
}
