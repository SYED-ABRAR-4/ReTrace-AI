from __future__ import annotations

import json
import os
from typing import Any

import httpx


class BaseProvider:
    def analyze(self, *, question: str, repo: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        raise NotImplementedError


class OllamaProvider(BaseProvider):
    def __init__(self, model: str | None = None, base_url: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")

    def is_available(self) -> bool:
        try:
            response = httpx.get(f"{self.base_url}/api/tags", timeout=4.0)
            if response.status_code != 200:
                return False
            tags = response.json()
            return bool(tags.get("models"))
        except Exception:
            return False

    def analyze(self, *, question: str, repo: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        repo_name = repo.get("full_name") or repo.get("name") or "repository"
        prompt = (
            "You are reconstructing a code decision from public repository evidence. "
            "Return valid JSON with keys: decision, facts, inferences, unknowns, timeline, affected_files, confidence, model_used. "
            f"Repository: {repo_name}. Question: {question}. Evidence: {json.dumps(evidence[:5], ensure_ascii=False)}"
        )

        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        text = payload.get("response", "")
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                parsed.setdefault("model_used", self.model)
                return parsed
        except Exception:
            pass
        return {
            "decision": "Local open-weight model did not return a usable structured result.",
            "facts": ["Repository metadata and public evidence were collected successfully."],
            "inferences": ["The system attempted to use Ollama for a more contextual reconstruction."],
            "unknowns": ["Insufficient evidence to reconstruct this decision beyond the available public signals."],
            "timeline": [],
            "affected_files": [],
            "confidence": "low",
            "model_used": self.model,
        }


class HeuristicProvider(BaseProvider):
    def analyze(self, *, question: str, repo: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
        repo_name = repo.get("full_name") or repo.get("name") or "repository"
        summary = evidence[0].get("excerpt", "") if evidence else "No direct evidence was found."
        title = evidence[0].get("title", "Repository investigation") if evidence else "Repository investigation"

        decision = (
            f"The repository suggests the decision was driven by practical engineering trade-offs rather than a single explicit statement. "
            f"Based on the public evidence in {repo_name}, the likely rationale was to address maintainability, operational clarity, or user impact captured in the available history."
        )

        facts = [
            f"Public repository evidence for {repo_name} was collected successfully.",
            f"The strongest available signal was: {title}.",
        ]

        inferences = [
            "The implementation appears to reflect a practical response to a concrete problem surfaced in the repository history.",
            "The decision likely balances short-term implementation speed with long-term maintainability and reliability.",
        ]

        unknowns = [
            "There is not enough repository evidence to reconstruct a definitive historical rationale for every implementation detail.",
            "Insufficient evidence to reconstruct this decision." if "why" in question.lower() else "The exact motivations behind the original authors' trade-offs are not fully documented in the public history.",
        ]

        timeline = [
            {
                "stage": "Repository",
                "title": repo_name,
                "date": repo.get("pushed_at") or "unknown",
                "description": f"Repository metadata shows the project is active and publicly available for evidence collection.",
            }
        ]

        for item in evidence[:3]:
            timeline.append(
                {
                    "stage": item.get("source_type", "Evidence"),
                    "title": item.get("title", "Public evidence"),
                    "date": item.get("date", "unknown"),
                    "description": item.get("excerpt", summary)[:240],
                }
            )

        confidence = "medium" if len(evidence) >= 2 else "low"
        return {
            "decision": decision,
            "facts": facts,
            "inferences": inferences,
            "unknowns": unknowns,
            "timeline": timeline,
            "affected_files": [
                file_name for file_name in [item.get("title") for item in evidence[:3]] if file_name
            ],
            "confidence": confidence,
            "model_used": "local-heuristic",
        }


def get_provider() -> BaseProvider:
    provider = OllamaProvider()
    if provider.is_available():
        return provider
    return HeuristicProvider()
