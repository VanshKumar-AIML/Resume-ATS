import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const api = axios.create({ baseURL: API_BASE_URL });

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const register = (email, password, full_name) =>
  api.post("/auth/register", { email, password, full_name });

export const login = (email, password) => api.post("/auth/login", { email, password });

export const uploadResume = (file, jobDescription) => {
  const formData = new FormData();
  formData.append("file", file);
  if (jobDescription) formData.append("job_description", jobDescription);
  return api.post("/resumes/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

export const analyzeText = (resumeText, jobDescription) =>
  api.post("/resumes/analyze-text", {
    resume_text: resumeText,
    job_description: jobDescription || null,
  });

export const getResume = (id) => api.get(`/resumes/${id}`);

export const getHistory = () => api.get("/dashboard/history");

export const downloadResumeUrl = (id) => `${API_BASE_URL}/resumes/${id}/download`;

export default api;
