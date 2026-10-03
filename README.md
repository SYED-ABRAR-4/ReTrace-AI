# ReTrace AI

ReTrace AI is an open-source developer tool that reconstructs the historical reasoning behind a code change, design decision, or implementation choice using public repository evidence.

## What ReTrace AI does

ReTrace AI helps a developer answer questions such as:

- Why was this function implemented this way?
- Why was Redis introduced here?
- Why was this approach chosen instead of another option?

The app accepts a public GitHub repository URL and a user question, then collects relevant repository evidence, analyzes it, and returns a Decision Replay that explains what appears to have happened and how confidently it can be supported.

The project is intentionally focused on public evidence and transparent uncertainty. If the repository does not contain enough signal, the result clearly says: "Insufficient evidence to reconstruct this decision."

## The problem it solves

Open-source code often hides the reasoning behind decisions that shaped the final implementation. Developers see the resulting code, but not always the conversations, trade-offs, issues, or pull requests that led there.

ReTrace AI creates a lightweight, structured workflow for reconstructing those decisions from the repository itself:

- commits
- issues
- pull requests
- docs and README context
- code-level change signals

This helps developers understand historical context without guessing or inventing reasoning.

## How the Decision Replay workflow works

1. User enters a public GitHub repository URL and a technical question.
2. The backend parses the repository and fetches recent evidence from GitHub.
3. The system ranks and filters relevant signals based on the user question.
4. A local open-weight AI model analyzes the evidence and produces a structured result.
5. The application returns a Decision Replay with:
   - Decision
   - Facts
   - Inferences
   - Unknowns
   - Evidence cards
   - Timeline
   - Affected files
   - Confidence

This workflow is deliberately evidence-first. It distinguishes among:

- FACT: directly backed by repository evidence
- INFERENCE: a reasonable interpretation drawn from multiple signals
- UNKNOWN: not established by the evidence available

## Why the open-weight AI model is core to the project

The project is not a generic chatbot. The open-weight model is a central part of the product because it performs the evidence synthesis step that turns repository history into an interpretable Decision Replay.

The architecture is intentionally designed as:

Open-weight AI model -> Evidence analysis -> Decision reconstruction -> Developer outcome

This matters because the product is not just retrieving data; it is turning raw public history into a structured explanation. A local open-weight model keeps the project aligned with the hackathon requirement and supports future substitution with another locally hosted model.

## Technology stack

Frontend:
- React
- Vite
- JavaScript
- Modern developer-tool style UI

Backend:
- Python
- FastAPI

AI:
- Ollama for local open-weight model execution
- Modular model provider architecture
- Heuristic fallback when local model access is unavailable

GitHub integration:
- GitHub REST API
- Public repositories only for the MVP

Storage:
- In-memory/local structured JSON state for the MVP

## Project architecture

```text
frontend (React + Vite)
        |
        v
backend (FastAPI)
        |
        +--> GitHub Collector
        |
        +--> Local model provider (Ollama / fallback)
        |
        +--> Decision Replay response
```

Key modules:

- `frontend/`: user interface and request flow
- `backend/app/main.py`: API entrypoint
- `backend/app/models.py`: request/response schemas
- `backend/app/services/github_collector.py`: repository parsing and evidence collection
- `backend/app/services/model_provider.py`: open-weight model integration and fallback logic

## Installation and setup

### Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama installed locally

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ReTrace-AI
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
# source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Frontend setup

```bash
cd ../frontend
npm install
```

### 4. Environment variables

Copy the example environment file and customize it locally:

```bash
cd ..
copy .env.example .env
```

Then update `.env` with your local values. Important:

- never commit `.env`
- never commit GitHub tokens
- never commit API keys or secrets
- do not store secrets in frontend code

Example `.env` values:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest
GITHUB_TOKEN=
GITHUB_API_BASE_URL=https://api.github.com
```

## How to install and run Ollama and the selected model

### Install Ollama

Follow the official Ollama installation guide for your operating system:
- https://ollama.com/download

### Start Ollama

```bash
ollama serve
```

### Pull a supported local open-weight model

```bash
ollama pull llama3.2:latest
```

The project reads the model name from `OLLAMA_MODEL` in the environment. If Ollama is not running or the model is unavailable, the app falls back to a heuristic analysis.

## Run the app

### Start the backend

From the project root:

```bash
cd backend
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Start the frontend

In another terminal:

```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

Open the frontend in a browser:

```text
http://localhost:5173/
```

## Example usage

### API request

```bash
curl -X POST http://127.0.0.1:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/microsoft/vscode",
    "question": "Why was this implemented this way?"
  }'
```

### UI usage

1. Open the frontend.
2. Enter a public GitHub repository URL.
3. Enter a question such as: "Why was Redis introduced here?"
4. Click "ReTrace Decision".
5. Review the evidence, reasoning, timeline, and confidence output.

## Known limitations

- The MVP only supports public GitHub repositories.
- It does not attempt full repository indexing or deep historical mining.
- GitHub API rate limits may reduce the evidentiary signal available for large repositories.
- The local model may not always provide a historically precise interpretation if the repository lacks enough evidence.
- The system is intentionally conservative and should not invent missing context.
- The result is a reconstruction based on public signals, not a definitive statement of original author intent.

## Future improvements

- Better relevance ranking for commits, issues, and PRs
- More targeted code-context retrieval
- Better timeline reconstruction from issue-to-PR-to-commit chains
- More flexible model selection and provider abstraction
- Improved evidence confidence scoring
- Optional GitHub token support for higher-rate-limit workflows
- Additional exports for reports or JSON snapshots

## Security and publication checklist

Before publishing to a public GitHub repository:

- confirm `.env` is not committed
- confirm no GitHub tokens, secrets, or API keys are in source files
- confirm no frontend secrets were added
- confirm the repo uses a public license such as MIT
- confirm the README accurately describes the current prototype scope

## License

This project is open-source and released under the MIT License. See [LICENSE](./LICENSE).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).
