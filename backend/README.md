# CodeGuard V2 — Backend Architecture & Service Guide

CodeGuard V2 is an enterprise-grade hybrid AI code review engine combining deterministic static analysis (AST parsing, Tree-sitter, Radon, linters, dataflow taint tracking, and repository intelligence) with grounded Google Gemini Large Language Model (LLM) reasoning and Retrieval-Augmented Generation (RAG).

---

## 1. Core Architecture

```
GitHub PR / Snippet
       │
       ▼
Input Processing & Diff Parsing
       │
       ▼
Deterministic Static Analysis (AST + Linters + CFG + Call Graph + Dataflow / Taint)
       │
       ▼
Repository Intelligence & Feature Aggregation
       │
       ▼
RAG Semantic Retrieval (Gemini Embedding 2 + In-Memory Vector Store + Reranking)
       │
       ▼
Prompt Builder & Context Prioritizer
       │
       ▼
Google Gemini Reasoning (Gemini 3.6 Flash — JSON Structured Output)
       │
       ▼
Response Validation & Evidence Grounding
       │
       ▼
Confidence Engine & Review Merger
       │
       ▼
PostgreSQL Persistence & JSON Report Generation
       │
       ▼
FastAPI Client Response
```

### Key Architectural Components

- **Google Gemini 2.5 Flash (`gemini-2.5-flash`)**:
  Primary reasoning LLM used for evidence-based review synthesis, root cause analysis, and actionable remediation patch generation. Requests enforce deterministic structured JSON outputs and omit deprecated sampling parameters (`temperature`, `top_p`, `top_k`).
- **Google Gemini Embedding 2 (`gemini-embedding-2`)**:
  High-dimensional (768-dim) semantic embedding model powering the RAG knowledge ingestion and query retrieval pipeline.
- **In-Memory Vector Store**:
  Fast in-memory vector store with strict dimension validation and cosine similarity search for knowledge retrieval.
- **PostgreSQL**:
  Relational database used for review lifecycle persistence, file reports, findings storage, and pipeline execution trace telemetry.

---

## 2. Technology Stack

- **Framework**: FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings
- **LLM & Embeddings**: Google GenAI Python SDK (`google-genai`), Google Gemini 2.5 Flash, Gemini Embedding 2
- **Database & ORM**: PostgreSQL, SQLAlchemy 2.0, Alembic, psycopg2-binary
- **Static Analysis**: Python `ast`, Tree-sitter (`tree-sitter-python`), Radon, Pylint, Flake8, Bandit
- **Testing & Tooling**: Pytest, Pytest-Asyncio, HTTPX

---

## 3. Environment Configuration

Copy `.env.example` to `.env` and configure your environment variables:

```bash
cp .env.example .env
```

### Configuration Sections

#### Application
| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `CodeGuard` | Application display name |
| `APP_VERSION` | `2.0.0` | Application release version |
| `DEBUG` | `false` | Enable debug mode and verbose logging |
| `LOG_LEVEL` | `INFO` | Root logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ENVIRONMENT` | `development` | Deployment environment |

#### Database (PostgreSQL / Supabase)
| Variable | Default | Description |
|---|---|---|
| `POSTGRES_HOST` | `localhost` | PostgreSQL host (local dev fallback) |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_DB` | `codeguard` | Database name |
| `POSTGRES_USER` | `codeguard` | Database username |
| `POSTGRES_PASSWORD` | `your_postgres_password_here` | Database password placeholder |
| `DATABASE_URL` | *(Auto-constructed)* | Full SQLAlchemy connection string (Supabase Session Pooler on port 5432) |
| `ALEMBIC_DATABASE_URL` | `None` | Optional separate migration connection URI (falls back to `DATABASE_URL`) |
| `DB_POOL_SIZE` | `5` | SQLAlchemy connection pool size |
| `DB_MAX_OVERFLOW` | `5` | Maximum overflow connections beyond pool size |
| `DB_POOL_TIMEOUT` | `30` | Connection checkout timeout in seconds |
| `DB_POOL_RECYCLE` | `1800` | Connection recycle period in seconds (prevents stale pooler connections) |

> [!IMPORTANT]
> - **Hosted Provider**: Supabase is used as the hosted PostgreSQL provider.
> - **Session Pooler (port 5432)**: The Session Pooler URI is used for IPv4 compatibility and full session/prepared-statement support.
> - **Credentials**: `DATABASE_URL` must always be supplied via environment variables or `.env`. Never commit credentials to version control.

#### Google Gemini
| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | `your_gemini_api_key_here` | Google Gemini API Key |
| `GEMINI_PRIMARY_MODEL` | `gemini-2.5-flash` | Primary Gemini model for code review reasoning |
| `GEMINI_LLM_MODEL` | `gemini-2.5-flash` | Gemini model for code review reasoning |
| `GEMINI_FALLBACK_MODELS` | `gemini-3.5-flash-lite,gemini-3.5-flash,gemini-3.6-flash` | Fallback models list |
| `GEMINI_EMBEDDING_MODEL` | `gemini-embedding-2` | Gemini model for RAG knowledge embeddings |
| `GEMINI_API_BASE_URL` | `https://generativelanguage.googleapis.com` | Gemini API endpoint |
| `GEMINI_TIMEOUT` | `60` | Request timeout in seconds |
| `GEMINI_MAX_RETRIES` | `3` | Maximum retry attempts with backoff |

#### LLM Configuration
| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | Active LLM provider (`gemini` or `mock`) |
| `LLM_MODEL` | `gemini-2.5-flash` | Reasoning model identifier |
| `LLM_MAX_TOKENS` | `4096` | Maximum generation tokens |
| `LLM_TIMEOUT` | `60` | LLM invocation timeout |
| `LLM_MAX_RETRIES` | `3` | Maximum retry attempts |

#### RAG & Embeddings
| Variable | Default | Description |
|---|---|---|
| `RAG_ENABLED` | `true` | Enable RAG knowledge augmentation |
| `RAG_EMBEDDING_PROVIDER` | `gemini` | Embedding provider for RAG |
| `RAG_EMBEDDING_MODEL` | `gemini-embedding-2` | Embedding model for knowledge |
| `EMBEDDING_DIMENSION` | `768` | Vector dimensionality (768 for Gemini Embedding 2) |
| `RAG_TOP_K` | `10` | Initial retrieval count |
| `RAG_RERANK_TOP_K` | `5` | Reranked context count |
| `RAG_SIMILARITY_THRESHOLD`| `0.70` | Minimum cosine similarity threshold |
| `RAG_CACHE_ENABLED` | `true` | Enable LRU embedding cache |
| `RAG_VECTOR_STORE` | `memory` | Active vector backend |

---

## 4. Installation & Local Development

### Virtual Environment Setup

1. **Create and activate virtual environment**:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/macOS
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Migrations (Alembic)**:
   ```bash
   alembic upgrade head
   ```

4. **Run Application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Run Tests**:
   ```bash
   pytest -v
   ```

---

## 5. API Endpoints

- `GET /health` — Service health status check.
- `POST /review/pr` — Submit a GitHub Pull Request for full asynchronous review.
- `POST /review/snippet` — Submit an isolated code snippet for rapid static + AI review.
- `GET /review/{review_id}` — Retrieve status and completed ReviewReport for a review request.

---

## 6. Architecture Decisions & Guidelines

1. **Gemini 3.6 Flash Parameter Policy**:
   Gemini 3.6 Flash omits legacy sampling parameters (`temperature`, `top_p`, `top_k`). Structured output consistency is enforced through deterministic schema design and strict Pydantic model validation.
2. **Dimension Validation**:
   Vector stores validate input dimensions strictly against the configured model dimension (768). Incompatible vectors raise descriptive `ValueError` exceptions and prevent silent truncation or zero-padding.
3. **Telemetry & Secret Sanitization**:
   All telemetry logs automatically sanitize API keys (including `AIza...` and GitHub tokens), database connection passwords, and Bearer tokens before logging or persisting trace records.
