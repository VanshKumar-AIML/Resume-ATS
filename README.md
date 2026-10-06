# AI Resume Builder & ATS Score Predictor

A full-stack app that analyzes resumes, predicts ATS (Applicant Tracking
System) compatibility, compares a resume against a job description, **builds
resumes from public profile links**, **suggests content enhancements**, and
**recommends certificates and study material (free & paid) ranked by how
well they fit the user's resume**.

## Stack

- **Frontend:** React (Vite)
- **Backend:** FastAPI (Python)
- **ML/NLP:** Scikit-learn, TF-IDF similarity, rule-based skill extraction,
  optional LLM enhancement (OpenAI / Hugging Face)
- **Database:** PostgreSQL (SQLAlchemy ORM; SQLite fallback for local dev)
- **Auth:** JWT
- **Deployment:** Docker Compose

## Folder Structure

```
Resume-ATS/
├── frontend/                      React app
│   └── src/
│       ├── api.js                 axios client (all endpoints)
│       ├── App.jsx                routes
│       ├── main.jsx
│       ├── index.css
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── ScoreCard.jsx
│       │   ├── TemplateCard.jsx        (new)
│       │   ├── CertificateCard.jsx     (new)
│       │   └── MaterialFilter.jsx      (new)
│       └── pages/
│           ├── Login.jsx
│           ├── Register.jsx
│           ├── Upload.jsx
│           ├── Results.jsx
│           ├── Dashboard.jsx
│           ├── BuildFromLinks.jsx      (new)
│           ├── Templates.jsx           (new)
│           ├── Enhancer.jsx            (new)
│           └── Learn.jsx               (new)
├── backend/                       FastAPI app
│   ├── main.py                    app entrypoint + router registration
│   ├── auth.py                    JWT + password hashing
│   ├── database.py                SQLAlchemy engine/session
│   ├── models.py                  User, Resume, AnalysisResult, ProfileLink
│   ├── schemas.py                 Pydantic request/response models
│   ├── file_extractor.py          PDF/DOCX -> plain text
│   ├── pdf_generator.py           template-aware PDF rendering
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── resume_routes.py
│   │   ├── dashboard_routes.py
│   │   ├── profile_routes.py           (new)
│   │   ├── enhancer_routes.py          (new)
│   │   ├── learn_routes.py             (new)
│   │   └── template_routes.py          (new)
│   └── templates/                      (new) resume template definitions
│       ├── classic.json
│       ├── modern.json
│       ├── minimal.json
│       └── technical.json
├── ml/
│   ├── keyword_extractor.py       section + skill extraction
│   ├── similarity.py              TF-IDF resume vs JD match + gaps
│   ├── predictor.py               ATS score model
│   ├── profile_parser.py          (new) fetch/normalize profile links
│   ├── resume_enhancer.py         (new) rule-based + optional LLM tips
│   ├── certificate_recommender.py (new) rank certificates by resume fit
│   └── study_material.py          (new) rank courses/videos by resume fit
├── data/                          (new) curated catalogs
│   ├── certificates.json
│   └── study_materials.json
├── database/
│   └── schema.sql
├── uploads/                       uploaded resumes + generated PDFs
└── docker-compose.yml
```

## How It Works

1. User registers / logs in (JWT-based auth).
2. User does one of:
   - uploads a resume (PDF/DOCX),
   - builds one from scratch in the UI, or
   - **imports public profile links (GitHub, GitLab, LeetCode, ...) to
     pre-fill a resume draft**.
3. User optionally pastes a job description.
4. Backend extracts plain text (`backend/file_extractor.py`).
5. `ml/keyword_extractor.py` extracts sections and matches known skills.
6. `ml/predictor.py` builds a feature vector and predicts an ATS score (0–100).
7. `ml/similarity.py` compares the resume against the job description
   (TF-IDF + skill overlap) to compute a match % and missing-keyword list.
8. Frontend shows the score, match %, and missing keywords.
9. User can:
   - pick a **resume template** and download a polished PDF,
   - run the **enhancer** for rewritten bullets, weak-phrase detection,
     missing-section warnings, and quantification gaps,
   - open the **Learn** page to see **certificates and study material
     ranked by fit for their resume**, filtered by cost (free / paid),
     platform, level, duration, and providers.
10. Every analysis is saved as a new "version" so the dashboard can show
    score improvement over time.

## Feature Details

### Resume Templates
- Template definitions live in `backend/templates/*.json`. Each JSON controls
  font family, accent color, and section order.
- `GET /templates` — list all templates.
- `GET /templates/{id}` — fetch one template definition.
- `POST /templates/{id}/render` — render a resume dict into a PDF using the
  template and return the file.

### Build Resume From Profile Links
- `POST /profile/import` — accepts `{ "urls": [...] }`.
- GitHub and GitLab: full support via public REST APIs.
- LeetCode: public GraphQL.
- LinkedIn: **unsupported** (ToS prohibits scraping); the endpoint returns a
  clear message pointing the user to LinkedIn's official "Save to PDF" export.
- Multiple links are merged into one draft (name, bio, skills, projects,
  warnings for any link that failed).

### Resume Enhancer
- `POST /enhancer/suggest` — body `{ "resume_text": "...", "job_description": "..." }`.
- Rule-based, always available:
  - weak-phrase detection,
  - bullet rewriting with strong action verbs,
  - missing-section warnings,
  - quantification-gap detection (bullets with no numbers, %, or $).
- LLM-based (optional) suggestions added when `LLM_PROVIDER` is set.

### Certificate Recommendations
- `POST /learn/certificates` — body includes `resume_text` (or `resume_skills`),
  plus filters: `free_only`, `max_cost`, `level`, `providers`, `top_k`.
- Ranks entries in `data/certificates.json` using the same TF-IDF pipeline as
  JD matching, and returns `match_score`, `already_covered_skills`, and
  `new_skills_gained` per result.

### Study Material Recommender (Free & Paid)
- `POST /learn/materials` — body includes `resume_text` (or `resume_skills`),
  plus filters: `cost` (`free` / `paid` / `any`), `platforms`, `level`,
  `max_hours`, `top_k`.
- Ranks entries in `data/study_materials.json`.

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

## Environment Variables (backend/.env)

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres connection string (defaults to local SQLite) |
| `JWT_SECRET_KEY` | Secret for signing auth tokens |
| `FRONTEND_ORIGIN` | Allowed CORS origin for the frontend |
| `GITHUB_TOKEN` | Optional — raises GitHub API rate limit |
| `LLM_PROVIDER` | `openai` / `hf` / `none` (default `none`) |
| `OPENAI_API_KEY` | Required if `LLM_PROVIDER=openai` |
| `HF_API_KEY` | Required if `LLM_PROVIDER=hf` |

## API Summary

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register` | Create a new user |
| POST | `/auth/login` | Obtain JWT |
| POST | `/resumes/upload` | Upload PDF/DOCX, extract text, run analysis |
| POST | `/resumes/analyze-text` | Analyze a resume built in the UI |
| GET  | `/resumes/{id}` | Fetch one resume + analysis |
| GET  | `/resumes/{id}/download` | Download optimized PDF |
| GET  | `/dashboard/history` | List versions + scores |
| POST | `/profile/import` | Import profile links into a resume draft |
| POST | `/enhancer/suggest` | Get resume enhancement suggestions |
| POST | `/learn/certificates` | Rank certificates by resume fit |
| POST | `/learn/materials` | Rank study material (free/paid filter) |
| GET  | `/templates` | List resume templates |
| GET  | `/templates/{id}` | Fetch one template |
| POST | `/templates/{id}/render` | Render resume as PDF in that template |

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
- `certificate_recommender.py` and `study_material.py` reuse the same
  TF-IDF approach, ranking catalog entries by cosine similarity against
  the resume text plus its extracted skills.
- `resume_enhancer.py` is rule-based by default. Setting `LLM_PROVIDER`
  enables OpenAI / Hugging Face suggestions on top of the rule-based output.

## Notes on the Catalogs

- `data/certificates.json` and `data/study_materials.json` ship with starter
  entries. Both are plain JSON arrays — grow them freely; the rankers handle
  any size. Each entry uses the same fields shown in the files themselves.

## Limitations

- **LinkedIn cannot be scraped.** LinkedIn's Terms of Service prohibit it,
  and the `/profile/import` endpoint returns an explicit `unsupported`
  status for LinkedIn URLs rather than attempting it. Users should use
  LinkedIn's official export and upload the PDF through the standard flow.
- **ORCID / Google Scholar** are recognized as link types but not yet fully
  parsed; they return a manual-review notice.
- **Template rendering** depends on `backend/pdf_generator.py`. Templates
  control layout metadata; the generator must read it. If you add a new
  template, make sure the generator supports the fields you use.

## Tested

- Backend: register → login → analyze-text → dashboard history → PDF
  download, verified end-to-end with FastAPI's TestClient.
- Frontend: `npm run build` verified to compile cleanly.
