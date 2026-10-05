import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getResume, downloadResumeUrl } from "../api";
import ScoreCard from "../components/ScoreCard";

export default function Results() {
  const { id } = useParams();
  const [resume, setResume] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getResume(id)
      .then((res) => setResume(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Could not load results"));
  }, [id]);

  if (error) return <div className="page"><p className="error-text">{error}</p></div>;
  if (!resume) return <div className="page"><p>Loading results...</p></div>;

  const { analysis } = resume;

  return (
    <div className="page">
      <h2>Resume Analysis — Version {resume.version}</h2>

      <div className="score-row">
        <ScoreCard label="ATS Score" score={analysis?.ats_score} suffix="/100" />
        {analysis?.match_percentage !== null && analysis?.match_percentage !== undefined && (
          <ScoreCard label="Job Match" score={analysis.match_percentage} suffix="%" />
        )}
      </div>

      {analysis?.skills_found?.length > 0 && (
        <section>
          <h3>Skills Found</h3>
          <div className="tag-list">
            {analysis.skills_found.map((s) => (
              <span key={s} className="tag tag-neutral">{s}</span>
            ))}
          </div>
        </section>
      )}

      {analysis?.missing_keywords?.length > 0 && (
        <section>
          <h3>Missing Keywords (from Job Description)</h3>
          <div className="tag-list">
            {analysis.missing_keywords.map((k) => (
              <span key={k} className="tag tag-missing">{k}</span>
            ))}
          </div>
          <p className="hint-text">
            Consider adding these skills to your resume if you genuinely have experience with them.
          </p>
        </section>
      )}

      {resume.sections && (
        <section>
          <h3>Detected Sections</h3>
          <ul>
            {Object.keys(resume.sections).map((sec) => (
              <li key={sec}>{sec}</li>
            ))}
          </ul>
        </section>
      )}

      <a href={downloadResumeUrl(resume.id)} target="_blank" rel="noreferrer">
        <button>Download Optimized Resume (PDF)</button>
      </a>
    </div>
  );
}
