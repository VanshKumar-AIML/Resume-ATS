"""Fetch and normalize public profile data from various links."""
import os, re, json, httpx
from typing import Dict, Any, List

GITHUB_API = "https://api.github.com"
GITLAB_API = "https://gitlab.com/api/v4"
LEETCODE_API = "https://leetcode.com/graphql"

HEADERS = {"Accept": "application/json", "User-Agent": "Resume-ATS/1.0"}
if os.getenv("GITHUB_TOKEN"):
    HEADERS["Authorization"] = f"token {os.getenv('GITHUB_TOKEN')}"


class ProfileParser:
    SUPPORTED = ("github.com", "gitlab.com", "leetcode.com",
                 "kaggle.com", "orcid.org", "scholar.google")

    def parse(self, url: str) -> Dict[str, Any]:
        url = url.strip()
        if "github.com" in url:
            return self._github(url)
        if "gitlab.com" in url:
            return self._gitlab(url)
        if "leetcode.com" in url:
            return self._leetcode(url)
        if "linkedin.com" in url:
            return {
                "source": "linkedin",
                "status": "unsupported",
                "reason": ("LinkedIn's Terms of Service prohibit scraping. "
                           "Use LinkedIn's official 'Save to PDF' export and upload "
                           "it through the standard resume upload flow."),
            }
        return {"source": "unknown", "status": "unsupported", "url": url}

    # ---------- GitHub ----------
    def _github(self, url: str) -> Dict[str, Any]:
        m = re.search(r"github\.com/([^/?#]+)", url)
        if not m:
            return {"source": "github", "status": "error", "reason": "no username"}
        user = m.group(1)
        try:
            u = httpx.get(f"{GITHUB_API}/users/{user}", headers=HEADERS, timeout=15)
            u.raise_for_status()
            user_data = u.json()
            repos = httpx.get(
                f"{GITHUB_API}/users/{user}/repos?per_page=100&sort=updated",
                headers=HEADERS, timeout=15,
            ).json()
        except Exception as e:
            return {"source": "github", "status": "error", "reason": str(e)}

        languages: Dict[str, int] = {}
        projects: List[Dict[str, Any]] = []
        for r in repos:
            if r.get("fork"):
                continue
            if r.get("language"):
                languages[r["language"]] = languages.get(r["language"], 0) + 1
            if r.get("stargazers_count", 0) >= 1 or not r.get("fork"):
                projects.append({
                    "name": r["name"],
                    "description": r.get("description") or "",
                    "url": r["html_url"],
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language"),
                    "topics": r.get("topics", []),
                })

        top_langs = sorted(languages, key=languages.get, reverse=True)[:8]
        return {
            "source": "github",
            "status": "ok",
            "name": user_data.get("name") or user_data.get("login"),
            "bio": user_data.get("bio") or "",
            "location": user_data.get("location") or "",
            "blog": user_data.get("blog") or "",
            "skills": top_langs,
            "projects": projects[:12],
            "raw_counts": {
                "public_repos": user_data.get("public_repos", 0),
                "followers": user_data.get("followers", 0),
            },
        }

    # ---------- GitLab ----------
    def _gitlab(self, url: str) -> Dict[str, Any]:
        m = re.search(r"gitlab\.com/([^/?#]+)", url)
        if not m:
            return {"source": "gitlab", "status": "error", "reason": "no username"}
        user = m.group(1)
        try:
            u = httpx.get(f"{GITLAB_API}/users?username={user}", timeout=15).json()
            if not u:
                return {"source": "gitlab", "status": "error", "reason": "not found"}
            uid = u[0]["id"]
            projects = httpx.get(
                f"{GITLAB_API}/users/{uid}/projects?per_page=100", timeout=15
            ).json()
        except Exception as e:
            return {"source": "gitlab", "status": "error", "reason": str(e)}

        langs = {}
        projs = []
        for p in projects:
            if p.get("language"):
                langs[p["language"]] = langs.get(p["language"], 0) + 1
            projs.append({
                "name": p["name"],
                "description": p.get("description") or "",
                "url": p["web_url"],
                "stars": p.get("star_count", 0),
                "language": p.get("language"),
                "topics": p.get("topics", []),
            })
        return {
            "source": "gitlab",
            "status": "ok",
            "name": u[0].get("name"),
            "bio": u[0].get("bio") or "",
            "location": u[0].get("location") or "",
            "skills": sorted(langs, key=langs.get, reverse=True)[:8],
            "projects": projs[:12],
        }

    # ---------- LeetCode ----------
    def _leetcode(self, url: str) -> Dict[str, Any]:
        m = re.search(r"leetcode\.com/(?:u/)?([^/?#]+)", url)
        if not m:
            return {"source": "leetcode", "status": "error", "reason": "no username"}
        user = m.group(1)
        query = """
        query getUser($u:String!){ matchedUser(username:$u){
          username
          profile{ realName aboutMe userAvatar ranking }
          submitStats{ acSubmissionNum{ difficulty count } }
          languageProblemCount{ languageName problemsSolved }
        }}
        """
        try:
            r = httpx.post(LEETCODE_API, json={
                "query": query, "variables": {"u": user}
            }, headers={**HEADERS, "Content-Type": "application/json"}, timeout=15)
            data = r.json().get("data", {}).get("matchedUser") or {}
        except Exception as e:
            return {"source": "leetcode", "status": "error", "reason": str(e)}
        if not data:
            return {"source": "leetcode", "status": "error", "reason": "not found"}
        langs = [l["languageName"] for l in data.get("languageProblemCount", [])]
        return {
            "source": "leetcode",
            "status": "ok",
            "name": data["profile"].get("realName") or user,
            "bio": data["profile"].get("aboutMe") or "",
            "skills": langs,
            "projects": [],
            "raw_counts": {
                "ranking": data["profile"].get("ranking"),
                "solved": data.get("submitStats", {}).get("acSubmissionNum", []),
            },
        }


def merge_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple parsed profiles into one resume draft."""
    name = next((p.get("name") for p in profiles if p.get("name")), "")
    bio = next((p.get("bio") for p in profiles if p.get("bio")), "")
    location = next((p.get("location") for p in profiles if p.get("location")), "")
    skills, seen = [], set()
    projects = []
    for p in profiles:
        for s in p.get("skills", []):
            if s and s.lower() not in seen:
                seen.add(s.lower())
                skills.append(s)
        projects.extend(p.get("projects", []))
    return {
        "name": name,
        "bio": bio,
        "location": location,
        "skills": skills,
        "projects": projects,
        "sources": [p.get("source") for p in profiles if p.get("status") == "ok"],
        "warnings": [
            {"source": p.get("source"), "reason": p.get("reason")}
            for p in profiles if p.get("status") != "ok"
        ],
    }