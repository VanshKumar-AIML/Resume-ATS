"""Rule-based + optional LLM resume enhancement suggestions."""
import os, re
from typing import Dict, Any, List

WEAK_PHRASES = [
    "responsible for", "helped with", "worked on", "involved in",
    "assisted with", "duties included", "was tasked with",
]
STRONG_VERBS = [
    "Led", "Built", "Designed", "Shipped", "Reduced", "Increased",
    "Automated", "Optimized", "Launched", "Architected",
]
RECOMMENDED_SECTIONS = [
    "Summary", "Skills", "Experience", "Projects", "Education", "Certifications",
]


class ResumeEnhancer:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "none").lower()

    def suggest(self, resume_text: str, job_description: str = "") -> Dict[str, Any]:
        out = {
            "weak_phrases": self._weak_phrases(resume_text),
            "rewrite_suggestions": self._rewrites(resume_text),
            "missing_sections": self._missing_sections(resume_text),
            "quantification_gaps": self._quant_gaps(resume_text),
            "provider": self.provider,
        }
        if self.provider == "openai":
            out["llm_suggestions"] = self._openai(resume_text, job_description)
        elif self.provider == "hf":
            out["llm_suggestions"] = self._hf(resume_text, job_description)
        return out

    # ---- rule-based ----
    def _weak_phrases(self, text: str) -> List[Dict[str, str]]:
        found = []
        for line in text.splitlines():
            low = line.lower()
            for p in WEAK_PHRASES:
                if p in low:
                    found.append({"line": line.strip(), "phrase": p})
        return found

    def _rewrites(self, text: str) -> List[Dict[str, str]]:
        out = []
        for line in text.splitlines():
            low = line.lower()
            for p in WEAK_PHRASES:
                if p in low:
                    replacement = re.sub(
                        p, self._pick_verb(line), line, flags=re.IGNORECASE
                    ).strip()
                    out.append({"original": line.strip(), "suggested": replacement})
        return out

    def _pick_verb(self, line: str) -> str:
        low = line.lower()
        if any(k in low for k in ["team", "mentor", "manage"]):
            return "Led"
        if any(k in low for k in ["design", "ui", "api", "system"]):
            return "Designed"
        if any(k in low for k in ["test", "bug", "fix"]):
            return "Resolved"
        if any(k in low for k in ["code", "develop", "build"]):
            return "Built"
        return "Delivered"

    def _missing_sections(self, text: str) -> List[str]:
        low = text.lower()
        return [s for s in RECOMMENDED_SECTIONS if s.lower() not in low]

    def _quant_gaps(self, text: str) -> List[str]:
        """Lines without numbers, %, or $ often lack quantified impact."""
        gaps = []
        for line in text.splitlines():
            s = line.strip()
            if len(s) < 25 or not s.startswith(("-", "•", "*")):
                continue
            if not re.search(r"\d|%|\$", s):
                gaps.append(s)
        return gaps[:15]

    # ---- LLM (optional) ----
    def _openai(self, resume_text: str, jd: str) -> List[str]:
        try:
            from openai import OpenAI
            client = OpenAI()
            prompt = self._prompt(resume_text, jd)
            r = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
            )
            return r.choices[0].message.content.split("\n")
        except Exception as e:
            return [f"LLM error: {e}"]

    def _hf(self, resume_text: str, jd: str) -> List[str]:
        try:
            import httpx
            key = os.getenv("HF_API_KEY", "")
            r = httpx.post(
                "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2",
                headers={"Authorization": f"Bearer {key}"},
                json={"inputs": self._prompt(resume_text, jd),
                      "parameters": {"max_new_tokens": 400}},
                timeout=60,
            )
            return [r.json()[0]["generated_text"]]
        except Exception as e:
            return [f"LLM error: {e}"]

    def _prompt(self, resume_text: str, jd: str) -> str:
        return (
            "You are an expert resume coach. Improve the following resume. "
            "Return 6-10 concrete bullet-point suggestions.\n\n"
            f"RESUME:\n{resume_text[:6000]}\n\n"
            f"JOB DESCRIPTION (optional):\n{jd[:2000]}\n"
        )