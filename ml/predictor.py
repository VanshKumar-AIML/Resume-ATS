"""
predictor.py
------------
Predicts an ATS compatibility score (0-100) for a resume, using features
pulled from keyword_extractor.py and similarity.py.

Pipeline position: Step 6 of the workflow
    6. The ATS model predicts a score

Depends on:
    - keyword_extractor.py (section/skill features)
    - similarity.py         (match % vs job description, if provided)
    - ats_model.pkl         (trained sklearn model, loaded at runtime)

This file also includes a `train_dummy_model()` function so the pipeline is
runnable end-to-end before you have real labeled resume data. Replace it with
a training script against labeled (resume -> recruiter_shortlisted) data
once available.
"""

import os
import pickle
from typing import Dict, List, Optional

import numpy as np
from sklearn.ensemble import RandomForestRegressor

try:
    from .keyword_extractor import extract_all
    from .similarity import compute_match
except ImportError:  # allows `python predictor.py` standalone execution
    from keyword_extractor import extract_all
    from similarity import compute_match

MODEL_PATH = os.path.join(os.path.dirname(__file__), "ats_model.pkl")

# Canonical resume sections we expect. Order matters -- it defines the
# feature vector layout used by both training and inference.
EXPECTED_SECTIONS = [
    "summary", "skills", "experience", "education",
    "projects", "certifications", "achievements",
]


# ---------------------------------------------------------------------------
# Feature engineering
# ---------------------------------------------------------------------------

def build_feature_vector(resume_text: str, jd_text: Optional[str] = None) -> np.ndarray:
    """
    Convert raw resume text (+ optional job description) into a fixed-length
    numeric feature vector for the model.

    Features (in order):
        0-6   : presence of each expected section (1/0)  -> 7 features
        7     : total word count (normalized /1000)
        8     : number of skills found
        9     : has quantifiable achievements (naive: contains a digit + %) 1/0
        10    : match_percentage vs JD (0 if no JD provided)
    """
    extracted = extract_all(resume_text)
    sections = extracted["sections"]

    section_flags = [1.0 if s in sections else 0.0 for s in EXPECTED_SECTIONS]
    word_count_norm = min(extracted["word_count"] / 1000.0, 1.0)
    skill_count = len(extracted["skills"])
    has_quantified_results = 1.0 if any(
        ch.isdigit() for ch in resume_text
    ) and "%" in resume_text else 0.0

    if jd_text:
        match_report = compute_match(resume_text, jd_text)
        match_percentage = match_report["match_percentage"] / 100.0
    else:
        match_percentage = 0.0

    features = section_flags + [word_count_norm, skill_count, has_quantified_results, match_percentage]
    return np.array(features, dtype=float).reshape(1, -1)


# ---------------------------------------------------------------------------
# Model loading / dummy training fallback
# ---------------------------------------------------------------------------

def load_model(path: str = MODEL_PATH) -> RandomForestRegressor:
    """
    Load the trained ATS model from disk. If it doesn't exist yet, trains
    and saves a placeholder model on synthetic data so the pipeline still
    runs end-to-end during development.
    """
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)

    print(f"[predictor] No model found at {path}, training a placeholder model...")
    model = train_dummy_model()
    with open(path, "wb") as f:
        pickle.dump(model, f)
    return model


def train_dummy_model() -> RandomForestRegressor:
    """
    Trains a placeholder RandomForestRegressor on synthetic feature data so
    predict_score() works before real labeled resumes are available.

    Replace with a real training script once you have historical data, e.g.:
        (resume_features, recruiter_shortlisted_or_ATS_score) pairs.
    """
    rng = np.random.default_rng(42)
    n_samples = 500
    n_features = len(EXPECTED_SECTIONS) + 4  # matches build_feature_vector output

    X = rng.random((n_samples, n_features))
    # Synthetic target: weighted sum of features + noise, scaled to 0-100.
    weights = rng.uniform(0.5, 1.5, size=n_features)
    y = (X @ weights)
    y = 100 * (y - y.min()) / (y.max() - y.min())

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)
    return model


# ---------------------------------------------------------------------------
# Public prediction API
# ---------------------------------------------------------------------------

def predict_score(resume_text: str, jd_text: Optional[str] = None, model=None) -> Dict:
    """
    Main entry point used by the FastAPI backend.

    Returns:
        {
            "ats_score": float (0-100),
            "features": { ... },   # for explainability in the UI
        }
    """
    model = model or load_model()
    features = build_feature_vector(resume_text, jd_text)
    raw_score = model.predict(features)[0]
    ats_score = round(float(np.clip(raw_score, 0, 100)), 1)

    return {
        "ats_score": ats_score,
        "feature_vector": features.tolist()[0],
        "feature_names": EXPECTED_SECTIONS + [
            "word_count_norm", "skill_count", "has_quantified_results", "jd_match_pct"
        ],
    }


if __name__ == "__main__":
    sample_resume = """
    Summary
    Backend engineer with 3 years experience.

    Skills
    Python, FastAPI, PostgreSQL, Docker, Machine Learning

    Experience
    Backend Developer at TechCorp (2022-2024)
    - Improved API latency by 35% through caching and query optimization.

    Education
    B.Tech in Computer Science, 2022
    """

    sample_jd = """
    Looking for a Python backend engineer with FastAPI, PostgreSQL, and
    Kubernetes experience.
    """

    result = predict_score(sample_resume, sample_jd)
    print("ATS Score:", result["ats_score"])
