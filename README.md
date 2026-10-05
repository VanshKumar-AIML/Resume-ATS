# AI Resume Builder & ATS Score Predictor

A full-stack app that analyzes resumes, predicts ATS (Applicant Tracking
System) compatibility, and compares a resume against a job description to
surface missing keywords and a match percentage.

## Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **ML/NLP:** Scikit-learn, TF-IDF similarity, rule-based skill extraction
- **Database:** PostgreSQL (SQLAlchemy ORM; SQLite fallback for local dev)
- **Auth:** JWT
- **Deployment:** Docker Compose

## Folder Structure

```
Resume-ATS/
├── frontend/          React app (login, upload/build, results, dashboard)
├── backend/           FastAPI app (auth, upload, analysis, PDF generation)
│   └── routes/        auth_routes.py, resume_routes.py, dashboard_routes.py
├── ml/                keyword_extractor.py, similarity.py, predictor.py
├── database/          schema.sql (Postgres schema)
├── uploads/            uploaded resumes + generated PDFs (gitignored contents)
└── docker-compose.yml
```

## How It Works (Workflow)

1. User registers/logs in (JWT-based auth).
2. User uploads a resume (PDF/DOCX) or builds one from scratch in the UI.
3. User optionally pastes a job description.
4. Backend extracts plain text from the file (`backend/file_extractor.py`).
5. `ml/keyword_extractor.py` extracts sections (Summary, Skills, Experience...)
   and matches known skills.
6. `ml/predictor.py` builds a feature vector and predicts an ATS score (0-100).
7. `ml/similarity.py` compares resume vs job description (TF-IDF + skill
   overlap) to compute a match % and missing-keyword list.
8. The frontend displays the score, match %, and missing keywords.
9. User downloads a polished PDF via `backend/pdf_generator.py`.
10. Every analysis is saved as a new "version" so the dashboard can show
    score improvement over time.

## Running Locally (without Docker)

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if using Postgres; SQLite works out of the box
uvicorn main:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`.

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App available at `http://localhost:5173`.

## Running with Docker Compose

```bash
docker compose up --build
```
This starts Postgres, the FastAPI backend, and the React frontend together.
- Frontend: http://localhost:5173
- Backend API docs: http://localhost:8000/docs

## Database Setup (manual, without Docker)

If you're running Postgres yourself instead of relying on SQLAlchemy's
`create_all()`:
```bash
psql -U ats_user -d resume_ats -f database/schema.sql
```

## Notes on the ML Models

- `predictor.py` auto-trains a placeholder `RandomForestRegressor` on
  synthetic data the first time it runs (saved to `ml/ats_model.pkl`), so
  the pipeline works immediately. Replace `train_dummy_model()` with real
  training against labeled resume outcomes (e.g. recruiter-shortlisted
  vs. not) once you have that data. XGBoost is a natural upgrade here.
- `similarity.py` uses TF-IDF + cosine similarity as a fast baseline.
  Swap in Sentence-Transformers embeddings for higher-quality matching.
- `keyword_extractor.py` uses a static skills list + regex section
  detection. Swap in spaCy NER or a fine-tuned transformer for more robust
  extraction across varied resume formats.
- LLM-based features (auto-generated summaries, bullet-point rewriting,
  grammar suggestions) aren't wired in yet — the natural next step is a
  `ml/llm_suggestions.py` module calling a Hugging Face or OpenAI-compatible
  API, called from a new `/resumes/{id}/suggestions` endpoint.

## Environment Variables (backend/.env)

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string (defaults to local SQLite) |
| `JWT_SECRET_KEY` | Secret for signing auth tokens |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the frontend |

## Tested

- Backend: register → login → analyze-text → dashboard history → PDF
  download, verified end-to-end with FastAPI's TestClient.
- Frontend: `npm run build` verified to compile cleanly.
