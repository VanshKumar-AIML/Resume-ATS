"""Recommend courses / videos / free study material ranked by resume relevance."""
import json, os
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "study_materials.json")


class StudyMaterialRecommender:
    def __init__(self):
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            self.items: List[Dict[str, Any]] = json.load(f)

    def recommend(
        self,
        resume_skills: List[str],
        resume_text: str = "",
        cost: str = "any",          # "free" | "paid" | "any"
        platforms: List[str] | None = None,
        level: str | None = None,
        max_hours: float | None = None,
        top_k: int = 20,
    ) -> List[Dict[str, Any]]:
        pool = self.items

        if cost == "free":
            pool = [i for i in pool if i.get("cost", 0) == 0]
        elif cost == "paid":
            pool = [i for i in pool if i.get("cost", 0) > 0]

        if platforms:
            pset = {p.lower() for p in platforms}
            pool = [i for i in pool if i.get("platform", "").lower() in pset]

        if level:
            pool = [i for i in pool if i.get("level", "").lower() == level.lower()]

        if max_hours is not None:
            pool = [i for i in pool if (i.get("hours") or 0) <= max_hours]

        if not pool:
            return []

        query = " ".join(resume_skills) + " " + resume_text[:2000]
        docs = [self._doc(i) for i in pool]

        try:
            vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
            X = vec.fit_transform([query] + docs)
            sims = cosine_similarity(X[0:1], X[1:]).flatten()
        except ValueError:
            sims = [0.0] * len(pool)

        results = []
        for item, s in zip(pool, sims):
            results.append({
                **item,
                "match_score": round(float(s) * 100, 2),
            })
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_k]

    @staticmethod
    def _doc(i: Dict[str, Any]) -> str:
        return " ".join([
            i.get("title", ""),
            i.get("platform", ""),
            i.get("level", ""),
            " ".join(i.get("skills", [])),
            i.get("description", ""),
        ])