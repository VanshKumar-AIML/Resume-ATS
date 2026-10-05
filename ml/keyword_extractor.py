"""
keyword_extractor.py
---------------------
Extracts structured sections and skill keywords from raw resume text.

Pipeline position: Steps 4-5 of the workflow
    4. Backend extracts raw text from the uploaded resume (PDF/DOCX -> plain text)
    5. This module extracts skills and key sections from that text

Used by:
    - similarity.py      (needs resume skills + full text)
    - predictor.py        (needs section presence + skill counts as features)
"""

import re
from typing import Dict, List

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------

# Section headers we look for. Keys are canonical section names, values are
# regex patterns (case-insensitive) that could appear as a heading in a resume.
SECTION_PATTERNS = {
    "contact": r"(contact information|contact details)",
    "summary": r"(summary|professional summary|objective|profile)",
    "skills": r"(skills|technical skills|core competencies)",
    "experience": r"(experience|work experience|professional experience|employment history)",
    "education": r"(education|academic background|qualifications)",
    "projects": r"(projects|personal projects|academic projects)",
    "certifications": r"(certifications?|licenses?)",
    "achievements": r"(achievements|awards|honors)",
}

# A starter skills database. In production this should be loaded from a
# database table or a larger curated file (e.g. skills_db.json) so it can be
# updated without redeploying code.
DEFAULT_SKILLS_DB: List[str] = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql",
    # Web / frontend
    "react", "angular", "vue", "html", "css", "next.js", "redux",
    # Backend / frameworks
    "fastapi", "django", "flask", "node.js", "express", "spring boot",
    # ML / data
    "machine learning", "deep learning", "nlp", "natural language processing",
    "scikit-learn", "tensorflow", "pytorch", "pandas", "numpy", "transformers",
    "hugging face", "computer vision",
    # Databases
    "postgresql", "mongodb", "mysql", "redis", "elasticsearch",
    # DevOps / cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "git", "github actions",
    # Soft / general
    "rest api", "microservices", "agile", "scrum", "system design",
]


# ---------------------------------------------------------------------------
# Section extraction
# ---------------------------------------------------------------------------

def extract_sections(text: str) -> Dict[str, str]:
    """
    Split resume text into labeled sections based on common headings.

    Returns a dict like:
        {"skills": "...", "experience": "...", "education": "...", ...}
    Any section not found in the text is simply omitted from the result.
    """
    # Build a single regex that matches any known heading, capturing which
    # canonical section it belongs to via named groups.
    combined_pattern = "|".join(
        f"(?P<{name}>^\\s*{pattern}\\s*:?\\s*$)"
        for name, pattern in SECTION_PATTERNS.items()
    )
    heading_re = re.compile(combined_pattern, re.IGNORECASE | re.MULTILINE)

    matches = list(heading_re.finditer(text))
    sections: Dict[str, str] = {}

    for i, match in enumerate(matches):
        section_name = match.lastgroup
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if content:
            sections[section_name] = content

    return sections


# ---------------------------------------------------------------------------
# Skill extraction
# ---------------------------------------------------------------------------

def extract_skills(text: str, skills_db: List[str] = None) -> List[str]:
    """
    Match known skills against the resume text (case-insensitive, whole-word).

    For a production system, swap this out for (or combine with) a
    transformer-based NER model (e.g. a fine-tuned spaCy/HF model) to catch
    skills not present in the static list.
    """
    skills_db = skills_db or DEFAULT_SKILLS_DB
    text_lower = text.lower()
    found = []

    for skill in skills_db:
        # word-boundary match so "go" doesn't match inside "algorithm"
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            found.append(skill)

    return sorted(set(found))


def extract_all(text: str, skills_db: List[str] = None) -> Dict:
    """
    Convenience wrapper: run section + skill extraction in one call and
    return a single structured payload the rest of the pipeline can consume.
    """
    sections = extract_sections(text)
    # Prefer extracting skills just from the "skills" section if present,
    # but fall back to the whole resume so nothing is missed.
    skill_source = sections.get("skills", text)
    skills = extract_skills(skill_source, skills_db)
    all_text_skills = extract_skills(text, skills_db)

    return {
        "sections": sections,
        "skills": sorted(set(skills) | set(all_text_skills)),
        "section_count": len(sections),
        "word_count": len(text.split()),
    }


if __name__ == "__main__":
    sample_resume = """
    Summary
    Software engineer with 3 years of experience building web applications.

    Skills
    Python, React, FastAPI, PostgreSQL, Docker, Machine Learning

    Experience
    Backend Developer at TechCorp (2022-2024)
    - Built REST APIs using FastAPI and PostgreSQL
    - Deployed services with Docker and AWS

    Education
    B.Tech in Computer Science, 2022
    """

    result = extract_all(sample_resume)
    print("Sections found:", list(result["sections"].keys()))
    print("Skills found:", result["skills"])
    print("Word count:", result["word_count"])
