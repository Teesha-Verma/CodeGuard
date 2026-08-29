# CodeGuard V2 — Hybrid AI Code Review Engine

CodeGuard V2 is an advanced, production-grade hybrid AI code review engine. It combines deterministic static analysis (AST parsing, Tree-sitter, Radon, linters, call graph, and dataflow taint tracking) with grounded Google Gemini Large Language Model (LLM) reasoning and RAG knowledge retrieval to detect bugs, explain root causes, and suggest actionable fixes in Pull Requests and code snippets.

## Architecture Overview

```
GitHub PR / Snippet
       │
       ▼
Input Processing
       │
       ▼
AST + Linters + CFG + Call Graph + Dataflow / Taint
       │
       ▼
Repository Intelligence + Feature Aggregation
       │
       ▼
Gemini Embedding 2 (RAG Retrieval + Reranking)
       │
       ▼
Prompt Builder
       │
       ▼
Gemini 3.6 Flash (Evidence-Based Review & Structured Output)
       │
       ▼
Confidence Engine & Merger
       │
       ▼
PostgreSQL Persistence + JSON Report
       │
       ▼
FastAPI Response
```

## Technology Stack

- **Reasoning LLM**: Google Gemini 2.5 Flash (`gemini-2.5-flash`) via `google-genai` SDK
- **Embedding Provider**: Google Gemini Embedding 2 (`gemini-embedding-2`, 768 dimensions)
- **Framework**: FastAPI, Uvicorn, Pydantic v2
- **Database**: PostgreSQL with SQLAlchemy 2.0
- **Vector Store**: In-memory vector store with strict dimension validation
- **Static Analysis**: Python AST, Tree-sitter, Radon, Pylint, Flake8, Bandit

## Quickstart

### Prerequisites
- Python 3.11+
- Google Gemini API Key (`GEMINI_API_KEY`)
- Docker & Docker Compose (for PostgreSQL)

### Setup
1. Clone the repository and navigate to `backend/`:
   ```bash
   cd backend
   ```
2. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp .env.example .env
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start database services:
   ```bash
   docker compose up -d
   ```
5. Run the application:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### API Endpoints
- `GET /health` — Health check endpoint.
- `POST /review/pr` — Submits a GitHub Pull Request for asynchronous review.
- `POST /review/snippet` — Analyzes a raw code snippet for rapid testing.
- `GET /review/{review_id}` — Fetches the status and results of a review.

### Running Tests
```bash
pytest -v
```
