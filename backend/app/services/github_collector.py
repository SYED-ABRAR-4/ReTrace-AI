from __future__ import annotations

import json
import re
from typing import Any

import httpx


class GitHubCollector:
    def __init__(self, base_url: str = "https://api.github.com"):
        self.base_url = base_url.rstrip("/")

    def parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        match = re.search(r"github\.com[:/]+([^/]+)/([^/]+?)(?:\.git)?/?$", repo_url.strip())
        if not match:
            raise ValueError("Provide a valid public GitHub repository URL.")
        return match.group(1), match.group(2)

    def _get_json(self, path: str, params: dict[str, Any] | None = None) -> Any:
        with httpx.Client(timeout=15.0, headers={"Accept": "application/vnd.github+json"}) as client:
            response = client.get(f"{self.base_url}{path}", params=params)
            response.raise_for_status()
            return response.json()

    def _safe_get_json(self, path: str, params: dict[str, Any] | None = None, fallback: Any | None = None) -> Any:
        try:
            return self._get_json(path, params)
        except httpx.HTTPStatusError:
            return fallback
        except Exception:
            return fallback

    def collect(self, repo_url: str, question: str) -> dict[str, Any]:
        owner, repo = self.parse_repo_url(repo_url)
        repo_name = f"{owner}/{repo}"
        metadata = self._safe_get_json(f"/repos/{owner}/{repo}", fallback={
            "full_name": repo_name,
            "html_url": repo_url,
            "updated_at": None,
            "description": "GitHub API rate limit prevented a fuller repository scan in the local MVP.",
        })
        commits = self._safe_get_json(f"/repos/{owner}/{repo}/commits", {"per_page": 5}, fallback=[])
        issues = self._safe_get_json(f"/repos/{owner}/{repo}/issues", {"state": "all", "per_page": 5}, fallback=[])
        pulls = self._safe_get_json(f"/repos/{owner}/{repo}/pulls", {"state": "all", "per_page": 5}, fallback=[])

        readme = None
        try:
            readme = self._safe_get_json(f"/repos/{owner}/{repo}/readme")
        except Exception:
            readme = None

        evidence = self._build_evidence(metadata, commits, issues, pulls, readme, question)
        affected_files = self._extract_affected_files(commits)
        return {
            "metadata": metadata,
            "evidence": evidence,
            "affected_files": affected_files,
            "repo": {"owner": owner, "repo": repo, "full_name": metadata.get("full_name", repo_name)},
        }

    def _build_evidence(self, metadata: dict[str, Any], commits: list[dict], issues: list[dict], pulls: list[dict], readme: dict | None, question: str) -> list[dict[str, str]]:
        question_terms = self._tokenize(question)
        evidence: list[dict[str, str]] = []

        for commit in commits[:4]:
            message = (commit.get("commit", {}) or {}).get("message", "") or "Repository update"
            if self._matches_terms(message, question_terms):
                evidence.append(
                    {
                        "source_type": "Commit",
                        "title": message.split("\n", 1)[0][:80],
                        "excerpt": message,
                        "link": commit.get("html_url") or metadata.get("html_url", ""),
                        "date": (commit.get("commit", {}) or {}).get("author", {}).get("date", "unknown"),
                        "relevance": "High",
                    }
                )

        for item in issues[:3]:
            if "pull_request" in item:
                continue
            title = item.get("title") or "Issue discussion"
            body = (item.get("body") or "")[:220]
            if self._matches_terms(f"{title} {body}", question_terms) or not evidence:
                evidence.append(
                    {
                        "source_type": "Issue",
                        "title": title,
                        "excerpt": body or "Issue discussion without a body.",
                        "link": item.get("html_url") or metadata.get("html_url", ""),
                        "date": item.get("created_at") or "unknown",
                        "relevance": "Medium",
                    }
                )

        for pr in pulls[:3]:
            title = pr.get("title") or "Pull request"
            body = (pr.get("body") or "")[:220]
            if self._matches_terms(f"{title} {body}", question_terms) or not evidence:
                evidence.append(
                    {
                        "source_type": "Pull Request",
                        "title": title,
                        "excerpt": body or "Proposal and review discussion.",
                        "link": pr.get("html_url") or metadata.get("html_url", ""),
                        "date": pr.get("created_at") or "unknown",
                        "relevance": "High",
                    }
                )

        if readme and isinstance(readme, dict):
            content = self._readme_excerpt(readme)
            if self._matches_terms(content, question_terms) or not evidence:
                evidence.append(
                    {
                        "source_type": "Documentation",
                        "title": "Repository documentation",
                        "excerpt": content,
                        "link": metadata.get("html_url", "") + "/blob/HEAD/README.md",
                        "date": metadata.get("updated_at") or "unknown",
                        "relevance": "Medium",
                    }
                )

        if not evidence:
            evidence.append(
                {
                    "source_type": "Code",
                    "title": "Repository summary",
                    "excerpt": f"Public repository {metadata.get('full_name', 'unknown')} was inspected to understand recent implementation signals and project context.",
                    "link": metadata.get("html_url") or "https://github.com",
                    "date": metadata.get("updated_at") or "unknown",
                    "relevance": "Low",
                }
            )

        return evidence[:6]

    def _extract_affected_files(self, commits: list[dict]) -> list[str]:
        files: list[str] = []
        for commit in commits[:5]:
            for file in commit.get("files", []) or []:
                path = file.get("filename")
                if path and path not in files:
                    files.append(path)
        return files

    def _readme_excerpt(self, readme: dict) -> str:
        raw_url = readme.get("download_url")
        if not raw_url:
            return "README documentation was available but no readable content was returned by the GitHub API."
        try:
            response = httpx.get(raw_url, timeout=10.0)
            response.raise_for_status()
            text = response.text
        except Exception:
            return "Repository documentation could not be downloaded in the local MVP."
        cleaned = re.sub(r"\s+", " ", text)
        return cleaned[:260]

    def _tokenize(self, text: str) -> set[str]:
        tokens = re.findall(r"[A-Za-z0-9]+", (text or "").lower())
        return {token for token in tokens if len(token) > 2}

    def _matches_terms(self, text: str, terms: set[str]) -> bool:
        if not terms:
            return True
        lowered = (text or "").lower()
        return any(term in lowered for term in terms)

    def json_dump(self, payload: dict[str, Any]) -> str:
        return json.dumps(payload, ensure_ascii=False, indent=2)
