"""Rank certificates from data/certificates.json against a resume's skills."""
import json, os
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "certificates.json")


class CertificateRecommender:
    def __init__(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            self.certs: List[Dict[str, Any]] = json.load(f)

    def recommend(
        self,
        resume_skills: List[str],
        resume_text: str = "",
        free_only: bool = False,
        max_cost: float | None = None,
        level: str | None = None,
        providers: List[str] | None = None,
        top_k: int = 15,
    ) -> List[Dict[str, Any]]:
        pool = self.certs

        if free_only:
            pool = [c for c in pool if c.get("cost", 0) == 0]
        if max_cost is not None:
            pool = [c for c in pool if c.get("cost", 0) <= max_cost]
        if level:
            pool = [c for c in pool if c.get("level", "").lower() == level.lower()]
        if providers:
            prov = {p.lower() for p in providers}
            pool = [c for c in pool if c.get("provider", "").lower() in prov]

        if not pool:
            return []

        query = " ".join(resume_skills) + " " + resume_text[:2000]
        docs = [self._doc(c) for c in pool]

        try:
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            X = vec.fit_transform([query] + docs)
            sims = cosine_similarity(X[0:1], X[1:]).flatten()
        except ValueError:
            sims = [0.0] * len(pool)

        results = []
        for c, s in zip(pool, sims):
            covered = [sk for sk in c.get("skills", [])
                       if sk.lower() in {r.lower() for r in resume_skills}]
            missing = [sk for sk in c.get("skills", [])
                       if sk.lower() not in {r.lower() for r in resume_skills}]
            results.append({
                **c,
                "match_score": round(float(s) * 100, 2),
                "already_covered_skills": covered,
                "new_skills_gained": missing,
            })

        results.sort(key=lambda x: (x["match_score"], -x.get("cost", 0)), reverse=True)
        return results[:top_k]

    @staticmethod
    def _doc(c: Dict[str, Any]) -> str:
        parts = [
            c.get("title", ""),
            c.get("provider", ""),
            c.get("level", ""),
            " ".join(c.get("skills", [])),
            c.get("description", ""),
        ]
        return " ".join(parts)