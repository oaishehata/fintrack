# FinTrack

Finance statement ingestion with an LLM-backed classifier and a React dashboard for upload, stats, duplicates, and recurring insights.

## Project Layout
- `ml_service/`: Flask API, Postgres access, CSV ingest, Ollama classification, stats.
- `frontend/`: Vite + React UI for upload and analytics.
- `docs/`: Architecture, backlog/stories, review rules.
- `tests/`: Unit and integration tests.

## Setup
### Backend
```bash
cd ml_service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt -r ../requirements-dev.txt
python app.py
```
Env vars (with defaults):
- `DB_HOST` (localhost), `DB_PORT` (5432), `DB_USER` (omar), `DB_PASSWORD` (postgres), `DB_NAME` (expense_db)
- `OLLAMA_URL` (http://127.0.0.1:11434/api/generate), `OLLAMA_MODEL` (phi3:mini)

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Tests
- Unit: `pytest tests/unit -q`
- Integration (API running): `pytest tests/integration -q`
- Frontend e2e (frontend running): `cd frontend && npx playwright test`

## Pre-commit
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Key Endpoints
- `POST /upload_csv` – ingest CSV and start classification
- `GET /stats` – totals, categories, duplicates, recurring, monthly trend
- `GET /classification_progress` – classification status
- `POST /reset` – truncate transactions
- `POST /classify` – force a classification run

## Docs
- `docs/architecture.md` – Mermaid diagram of data flow
- `docs/backlog.md` – backlog/stories
- `docs/review-rules.md` – PR expectations and checklist
