import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../api";

export default function Dashboard() {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getHistory()
      .then((res) => setHistory(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load history"));
  }, []);

  return (
    <div className="page">
      <h2>Your Resume Versions</h2>
      {error && <p className="error-text">{error}</p>}

      {history.length === 0 && !error && (
        <p>No resumes analyzed yet. <Link to="/upload">Analyze your first resume</Link>.</p>
      )}

      <table className="history-table">
        <thead>
          <tr>
            <th>Version</th>
            <th>ATS Score</th>
            <th>Job Match</th>
            <th>Date</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {history.map((h) => (
            <tr key={h.id}>
              <td>v{h.version}</td>
              <td>{h.ats_score ?? "-"}</td>
              <td>{h.match_percentage !== null && h.match_percentage !== undefined ? `${h.match_percentage}%` : "-"}</td>
              <td>{new Date(h.created_at).toLocaleDateString()}</td>
              <td><Link to={`/results/${h.id}`}>View</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
