from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    source_type: str = Field(..., example="Commit")
    title: str = Field(..., example="Add Redis cache integration")
    excerpt: str = Field(..., example="Introduce Redis-backed cache to improve read throughput.")
    link: str = Field(..., example="https://github.com/owner/repo/commit/abc123")
    date: str = Field(..., example="2024-03-12")
    relevance: str = Field(..., example="High")


class TimelineEvent(BaseModel):
    stage: str = Field(..., example="Issue")
    title: str = Field(..., example="Need for async caching")
    date: str = Field(..., example="2024-03-10")
    description: str = Field(..., example="The issue describes a performance problem before the change.")


class AnalyzeRequest(BaseModel):
    repo_url: str = Field(..., example="https://github.com/owner/repository")
    question: str = Field(..., example="Why was this implemented this way?")


class DecisionReplay(BaseModel):
    decision: str
    facts: list[str]
    inferences: list[str]
    unknowns: list[str]
    evidence: list[EvidenceItem]
    timeline: list[TimelineEvent]
    affected_files: list[str]
    confidence: Literal["low", "medium", "high"]
    model_used: str = Field(default="local-heuristic")


class RepoSummary(BaseModel):
    owner: str
    repo: str
    full_name: str
    description: str | None = None
    default_branch: str | None = None
    stars: int | None = None
    watchers: int | None = None
    html_url: str
    pushed_at: str | None = None
