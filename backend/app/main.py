from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import AnalyzeRequest, DecisionReplay
from app.services.github_collector import GitHubCollector
from app.services.model_provider import get_provider

app = FastAPI(title="ReTrace AI", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

collector = GitHubCollector()


@app.get("/health")
def health():
    return {"status": "ok", "service": "ReTrace AI"}


@app.post("/api/analyze", response_model=DecisionReplay)
def analyze(payload: AnalyzeRequest):
    try:
        repo_data = collector.collect(payload.repo_url, payload.question)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"GitHub lookup failed: {exc}") from exc

    provider = get_provider()
    analysis = provider.analyze(
        question=payload.question,
        repo=repo_data["metadata"],
        evidence=repo_data["evidence"],
    )

    replay = DecisionReplay(
        decision=analysis.get("decision", "Insufficient evidence to reconstruct this decision."),
        facts=analysis.get("facts", []),
        inferences=analysis.get("inferences", []),
        unknowns=analysis.get("unknowns", ["Insufficient evidence to reconstruct this decision."]),
        evidence=[
            {
                "source_type": item.get("source_type", "Code"),
                "title": item.get("title", "Repository signal"),
                "excerpt": item.get("excerpt", "No excerpt available."),
                "link": item.get("link", "https://github.com"),
                "date": item.get("date", "unknown"),
                "relevance": item.get("relevance", "Low"),
            }
            for item in repo_data["evidence"]
        ],
        timeline=[
            {
                "stage": event.get("stage", "Evidence"),
                "title": event.get("title", "Repository event"),
                "date": event.get("date", "unknown"),
                "description": event.get("description", "Public history indicates a relevant signal."),
            }
            for event in analysis.get("timeline", [])
        ],
        affected_files=repo_data.get("affected_files", []),
        confidence=analysis.get("confidence", "low"),
        model_used=analysis.get("model_used", "local-heuristic"),
    )

    return replay
