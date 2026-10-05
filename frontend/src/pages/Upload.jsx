import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadResume, analyzeText } from "../api";

export default function Upload() {
  const [mode, setMode] = useState("upload"); // "upload" | "scratch"
  const [file, setFile] = useState(null);
  const [resumeText, setResumeText] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res =
        mode === "upload"
          ? await uploadResume(file, jobDescription)
          : await analyzeText(resumeText, jobDescription);
      navigate(`/results/${res.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <h2>Analyze Your Resume</h2>

      <div className="mode-toggle">
        <button className={mode === "upload" ? "active" : ""} onClick={() => setMode("upload")}>
          Upload Resume (PDF/DOCX)
        </button>
        <button className={mode === "scratch" ? "active" : ""} onClick={() => setMode("scratch")}>
          Build From Scratch
        </button>
      </div>

      <form onSubmit={handleSubmit} className="upload-form">
        {mode === "upload" ? (
          <input
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setFile(e.target.files[0])}
            required
          />
        ) : (
          <textarea
            placeholder={`Paste or write your resume text here.\n\nTip: use headings like "Summary", "Skills", "Experience", "Education" so the analyzer can find each section.`}
            rows={12}
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            required
          />
        )}

        <textarea
          placeholder="Paste a job description here (optional) to get a match % and missing keywords"
          rows={6}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
        />

        {error && <p className="error-text">{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Resume"}
        </button>
      </form>
    </div>
  );
}
