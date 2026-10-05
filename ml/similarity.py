"""
similarity.py
-------------
Compares a resume against a job description to compute a match percentage
and identify missing keywords.

Pipeline position: Step 7 of the workflow
    7. The similarity model compares the resume with the job description

Depends on:
    - keyword_extractor.py (to pull skills out of both texts)

Used by:
    - predictor.py (match_percentage is one of the ATS score features)
    - backend API   (to render "missing keywords" and "match %" in the UI)
"""

from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    from .keyword_extractor import extract_skills, DEFAULT_SKILLS_DB
except ImportError:  # allows `python similarity.py` standalone execution
    from keyword_extractor import extract_skills, DEFAULT_SKILLS_DB


# ---------------------------------------------------------------------------
# Text-level similarity (captures overall relevance, not just skill overlap)
# ---------------------------------------------------------------------------

def text_similarity(resume_text: str, jd_text: str) -> float:
    """
    Cosine similarity between TF-IDF vectors of resume and job description.
    Returns a float in [0, 1].

    Note: TF-IDF is a fast, dependency-light baseline. For higher accuracy,
    swap this for sentence embeddings (e.g. `sentence-transformers`,
    all-MiniLM-L6-v2) and cosine similarity on the embedding vectors.
    """
    if not resume_text.strip() or not jd_text.strip():
        return 0.0

    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform([resume_text, jd_text])
    score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    return round(float(score), 4)


# ---------------------------------------------------------------------------
# Skill-level gap analysis (what specifically is missing)
# ---------------------------------------------------------------------------

def keyword_gap(resume_text: str, jd_text: str, skills_db: List[str] = None) -> Dict[str, List[str]]:
    """
    Determine which skills mentioned in the JD are present/missing in the resume.
    """
    skills_db = skills_db or DEFAULT_SKILLS_DB

    resume_skills = set(extract_skills(resume_text, skills_db))
    jd_skills = set(extract_skills(jd_text, skills_db))

    matched = sorted(resume_skills & jd_skills)
    missing = sorted(jd_skills - resume_skills)

    return {
        "matched_keywords": matched,
        "missing_keywords": missing,
        "jd_skill_count": len(jd_skills),
        "resume_skill_count": len(resume_skills),
    }


# ---------------------------------------------------------------------------
# Combined match report
# ---------------------------------------------------------------------------

def compute_match(resume_text: str, jd_text: str, skills_db: List[str] = None) -> Dict:
    """
    Full comparison used by the API layer. Combines semantic text similarity
    with explicit skill-keyword overlap into one match percentage.

    Weighting: 60% skill overlap (recruiters/ATS care most about hard
    keyword matches), 40% overall text similarity (captures context/relevance
    beyond just skill nouns). Tune these weights against real labeled data.
    """
    gap = keyword_gap(resume_text, jd_text, skills_db)
    text_sim = text_similarity(resume_text, jd_text)

    if gap["jd_skill_count"] > 0:
        skill_overlap_ratio = len(gap["matched_keywords"]) / gap["jd_skill_count"]
    else:
        skill_overlap_ratio = 0.0

    match_score = (0.6 * skill_overlap_ratio) + (0.4 * text_sim)
    match_percentage = round(match_score * 100, 1)

    return {
        "match_percentage": match_percentage,
        "text_similarity": text_sim,
        "skill_overlap_ratio": round(skill_overlap_ratio, 4),
        **gap,
    }


if __name__ == "__main__":
    resume = """
    Skills: Python, FastAPI, PostgreSQL, Docker
    Experience: Built REST APIs and deployed with Docker on AWS.
    """
    job_description = """
    We are looking for a backend engineer skilled in Python, FastAPI,
    PostgreSQL, Kubernetes, and CI/CD. Experience with machine learning
    is a plus.
    """

    report = compute_match(resume, job_description)
    print("Match %:", report["match_percentage"])
    print("Matched:", report["matched_keywords"])
    print("Missing:", report["missing_keywords"])
