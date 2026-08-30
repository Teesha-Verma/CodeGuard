# CodeGuard V2 — Backend Architecture & Service Guide

CodeGuard V2 is an enterprise-grade hybrid AI code review engine that combines deterministic static analysis (AST parsing, Tree-sitter, Radon, linters, control flow graph construction, call graph analysis, dataflow taint tracking, and repository intelligence) with grounded **Groq Large Language Model (LLM)** reasoning and **Google Gemini Retrieval-Augmented Generation (RAG)** embeddings.

---

## 1. High-Level Architecture

```
                      GitHub PR / Code Snippet
                                │
                                ▼
                   Input Processing & Diff Parser
                    (Primary vs. Supporting Files)
                                │
                                ▼
       ┌─────────────────────────────────────────────────────────┐
       │             Deterministic Static Analysis Engine        │
       │  • Python AST & Heuristic Analyzers                     │
       │  • Flake8, PyLint, Bandit Security Linters              │
       │  • Control Flow Graph (CFG) & Cyclomatic Complexity     │
       │  • Interprocedural Call Graph Construction              │
       │  • Dataflow Graph & Taint Tracking Engine               │
       │  • Repository Intelligence (Architecture & Hotspots)    │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │       Two-Phase ReviewGenerator & LLM Selection         │
       │  [Phase A] Flat Finding Collection (All Analyzers)      │
       │  [Phase B] Normalized Fingerprint Deduplication         │
       │            Low-Signal Style Classification              │
       │            Priority & Confidence Calibration            │
       │            Budget-Capped LLM Candidate Selection        │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │             RAG Knowledge Augmentation Layer            │
       │  • Google Gemini Embedding 2 (768-dim Vectors)          │
       │  • In-Memory Vector Store with Cosine Similarity Search │
       │  • Two-Tier Knowledge Reranker (CWE / OWASP Standards)  │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │           Groq LLM Reasoning & Fallback Layer           │
       │  • Primary Model: llama-3.3-70b-versatile               │
       │  • Fallback Chain: llama-3.1-8b-instant, etc.           │
       │  • Rate-Limit & TPD Quota Fast-Switching (0 retries)   │
       │  • Bounded Localized Context (Target Line ± 50 lines)   │
       └────────────────────────────┬────────────────────────────┘
                                    │
                                    ▼
       ┌─────────────────────────────────────────────────────────┐
       │            Metrics Engine & Report Synthesis            │
       │  • Strict Invariant-Checked Summary Statistics          │
       │  • PostgreSQL / Supabase Multi-Category Persistence     │
       │  • ReviewReport Disk Caching & FastAPI Responses        │
       └─────────────────────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### 2.1. Two-Phase Review Generator & Deterministic LLM Selection

To eliminate line-order bias and prevent trivial formatting issues from consuming LLM quota, `ReviewGenerator` operates in three distinct phases:

1. **Phase A (Collection)**:
   - Gathers all raw static findings from AST rules, linters, heuristics, and dataflow taint analysis into a flat list (independent of source-code line order).
2. **Phase B (Deduplication, Classification & Selection)**:
   - **Normalized Deduplication**: Hashes finding identities (`file_path:line:issue_type:normalized_message`). Overlapping findings on the same line (e.g. Flake8 `E501` + PyLint `C0301`) merge into a single finding with combined `detection_sources: ["flake8", "pylint"]` and aggregated evidence.
   - **Centralized Style Classification**: Matches rule codes (Flake8 `E/W`, PyLint `C/R`, pydocstyle `D`) and message patterns (whitespace, line length, docstrings). Style findings are strictly classified as `is_low_signal = True`, `signal_priority = "low"`, and `reasoning_source = "static_analysis"`. They **never** consume LLM budget slots.
   - **Priority-Based Candidate Ranking**: Meaningful findings are ranked strictly by:
     1. Severity: `critical` (5) > `high` (4) > `medium` (3) > `low` (2) > `info` (1)
     2. Category: `security` (6) > `mutation risks` (5) > `async misuse` (4) > `runtime logic risks` (3) > `maintainability` (2) > `style` (1)
     3. Presence of dataflow / taint evidence
     4. Evidence strength & calibrated confidence score
   - **Budget Upper Bound**: Selects at most `LLM_MAX_GENERATION_REQUESTS_PER_REVIEW` (default: 25). If a review has only 5 meaningful findings, only 5 requests are made.
3. **Phase C (Reasoning & Assembly)**:
   - Selected candidates receive grounded Groq LLM reasoning.
   - Non-selected findings (style, below threshold, budget overflow) receive deterministic static explanations (`reasoning_source: static_analysis`).
   - If Groq reasoning fails or models are exhausted, the original static finding is preserved with `reasoning_source: static_analysis` (graceful degradation).

---

### 2.2. Groq LLM Reasoning & Fast Fallback Handling

- **Primary Reasoning Model**: `llama-3.3-70b-versatile` (configurable via `LLM_MODEL`).
- **Configured Fallback Models**: `llama-3.1-8b-instant`, `openai/gpt-oss-120b`, `qwen/qwen3.8-27b`, `groq/compound-mini`.
- **Intelligent 429 Error Discrimination**:
  - **Token-Per-Day (TPD) Quota Exhaustion**: When Groq returns a daily token limit error, the model is immediately marked permanently exhausted for the remainder of the review, retries are skipped (0 retry waste), and the pipeline instantly advances to the next fallback model.
  - **Transient Request Rate Limits (RPM / TPM)**: Retries with bounded backoff (1–2s).
- **Review-Aware Model State**: Once a model is exhausted in a review, all subsequent findings in that review skip the exhausted model automatically.
- **Per-Review Accounting**: `ReviewLLMTracker` monitors:
  - `llm_requests_attempted`, `llm_requests_succeeded`, `llm_requests_failed`
  - `llm_requests_skipped_low_signal`, `llm_requests_skipped_budget`
  - `llm_models_used`, `llm_tokens_requested`, `llm_tokens_used`

---

### 2.3. Google Gemini Embeddings & RAG Retrieval

- **Embedding Model**: `gemini-embedding-2` producing **768-dimensional** dense vectors via Google GenAI SDK.
- **Strict Dimension Validation**: Vector stores enforce 768-dim input validation, raising descriptive errors on dimension mismatches.
- **RAG Knowledge Base**: Curated OWASP ASVS, WSTG, CWE, and Python standard practice guides located in `app/analysis/RAG/knowledge/`.
- **Two-Tier Retrieval & Reranking**: Vector cosine similarity retrieval followed by rule-based heuristic reranking.

---

### 2.4. Static Analysis, Dataflow & Repository Intelligence

- **AST Rules & Analyzers**:
  - Dynamic execution (`eval`, `exec`, unsafe `subprocess`, unsafe `pickle`).
  - Runtime logic risks (mutable default arguments, collection mutation during iteration).
  - Scope issues (variable shadowing, unsafe global variable mutation).
  - Async pitfalls (unawaited coroutines, async misuse).
- **Control Flow Graph (CFG)**: Cyclomatic complexity calculation and cycle detection.
- **Call Graph**: Interprocedural caller/callee resolution.
- **Dataflow / Taint Tracking**: Source-to-sink vulnerability analysis (e.g. untrusted input reaching SQL execution or system commands).
- **Repository Intelligence**:
  - Architecture detection (MVC, Repository, Clean, Layered).
  - Risk hotspots (complexity, fan-in/fan-out coupling, centrality).
  - Layer rule violation checks.
  - Change impact analysis (affected modules, regression scope).
  - All repository models support comprehensive `to_dict()` JSON serialization.

---

### 2.5. Summary Statistics & Mathematical Invariants

`MetricsCalculator` enforces strict mathematical consistency across all reports:

| Field | Definition | Invariant Constraint |
|---|---|---|
| `total_issues` | Meaningful issues count (confidence ≥ 0.3, not low-signal) | `total_issues == meaningful_issues` |
| `meaningful_issues` | High-value correctness/security issues | `sum(by_severity.values()) == meaningful_issues` |
| `style_findings` | Formatting, whitespace, docstrings, linter conventions | `is_low_signal == True` |
| `suppressed_findings` | Low-confidence findings (confidence < 0.3) | `confidence < 0.3` |
| `total_all_issues` | Total count of all detected issues | `total_all_issues == meaningful + style + suppressed` |
| `by_severity` | Severity distribution for **meaningful issues only** | `sum(by_severity.values()) == meaningful_issues` |
| `all_by_severity` | Severity distribution for **all detected issues** | `sum(all_by_severity.values()) == total_all_issues` |
| `reasoning_sources` | Attribution breakdown (`llm` vs `static_analysis`) | `llm + static_analysis == total_all_issues` |

---

## 3. Technology Stack

- **API Framework**: FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings
- **LLM Reasoning**: Groq Python SDK (`groq`), Llama 3.3 70B Versatile, Llama 3.1 8B Instant
- **Embeddings & RAG**: Google GenAI SDK (`google-genai`), Gemini Embedding 2 (768-dim)
- **Database & ORM**: PostgreSQL (Supabase Session Pooler), SQLAlchemy 2.0, Alembic, psycopg2-binary
- **Static Analysis**: Python `ast`, Radon, Pylint, Flake8, Bandit
- **Testing & Verification**: Pytest, Pytest-Asyncio, HTTPX

---

## 4. Environment Configuration

Copy `.env.example` to `.env` and configure your credentials:

```bash
cp .env.example .env
```

### Key Configuration Variables

#### Application
| Variable | Default | Description |
|---|---|---|
| `APP_NAME` | `CodeGuard` | Application display name |
| `APP_VERSION` | `2.0.0` | Release version |
| `DEBUG` | `false` | Enable debug mode |
| `LOG_LEVEL` | `INFO` | Root logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `ENVIRONMENT` | `development` | Environment name |

#### Database (PostgreSQL / Supabase)
| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | *(Required)* | Full PostgreSQL connection URI (e.g. Supabase Session Pooler port 5432) |
| `DB_POOL_SIZE` | `5` | SQLAlchemy pool size |
| `DB_MAX_OVERFLOW` | `5` | Maximum pool overflow |
| `DB_POOL_TIMEOUT` | `30` | Connection timeout (seconds) |
| `DB_POOL_RECYCLE` | `1800` | Connection recycle period (seconds) |

#### Groq (LLM Reasoning & Generation)
| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | *(Required)* | Groq API Key |
| `LLM_PROVIDER` | `groq` | Active LLM provider (`groq`, `mock`) |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Primary reasoning model |
| `GROQ_FALLBACK_MODELS` | `llama-3.1-8b-instant` | Comma-separated fallback models |
| `LLM_MAX_GENERATION_REQUESTS_PER_REVIEW` | `25` | Upper-bound budget for LLM calls per review |
| `LLM_MAX_CONTEXT_LINES` | `50` | Maximum surrounding lines for prompt context |
| `LLM_MAX_CONTEXT_CHARS` | `4000` | Maximum character length for code context |
| `LLM_TIMEOUT` | `60` | LLM invocation timeout in seconds |
| `LLM_MAX_RETRIES` | `2` | Maximum retry attempts for transient errors |

#### Google Gemini (Embeddings Only)
| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(Required)* | Google Gemini API Key |
| `EMBEDDING_PROVIDER` | `gemini` | Embeddings provider |
| `EMBEDDING_MODEL` | `gemini-embedding-2` | Embedding model identifier |
| `EMBEDDING_DIMENSION` | `768` | Vector dimensionality (768 for Gemini Embedding 2) |

#### GitHub & Pipeline Timeouts
| Variable | Default | Description |
|---|---|---|
| `GITHUB_TOKEN` | *(Optional)* | GitHub Personal Access Token for PR reviews |
| `MAX_REVIEW_DURATION_SECONDS` | `300` | Maximum PR review deadline before partial finalization |
| `PIPELINE_TIMEOUT` | `300` | Overall pipeline execution timeout |

---

## 5. Installation & Local Development

### 5.1. Virtual Environment Setup

```bash
# 1. Create and activate virtual environment
python -m venv .venv

# Windows:
.\.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

### 5.2. Database Migrations

```bash
# Apply latest Alembic migrations to PostgreSQL / Supabase
alembic upgrade head
```

### 5.3. Running the Server

```bash
# Start FastAPI backend with Uvicorn hot-reloading
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The interactive API documentation is available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. API Endpoints

### `GET /health`
Returns service operational health status.

### `POST /review/snippet`
Analyzes a standalone Python code snippet synchronously.
```json
{
  "code": "def query(user_input):\n    eval(user_input)",
  "language": "python",
  "filename": "snippet.py"
}
```

### `POST /review/pr`
Queues an asynchronous review for a GitHub Pull Request.
```json
{
  "repo_url": "https://github.com/owner/repository",
  "pr_number": 42
}
```

### `GET /review/{review_id}`
Retrieves the review status and full `ReviewReport` containing:
- `file_reports`: Detailed findings categorized into `meaningful_issues`, `style_findings`, and `suppressed_findings`.
- `summary_stats`: Verified metrics (`total_issues`, `by_severity`, `reasoning_sources`).
- `trace_id`: Pipeline execution telemetry trace identifier.

---

## 7. Running Tests

Execute the complete test suite:

```bash
# Run all unit and pipeline verification tests
pytest tests/test_pipeline.py tests/test_finding_separation.py tests/test_source_attribution.py tests/test_repository_intelligence.py tests/test_grounding.py tests/test_pipeline_reasoning_fix.py -v

# Run dedicated pipeline reasoning and invariant tests
pytest tests/test_pipeline_reasoning_fix.py -v
```

---

## 8. Directory Structure

```
backend/
├── app/
│   ├── analysis/             # Static analysis & RAG subsystems
│   │   ├── dataflow/         # Dataflow graph & taint engine
│   │   ├── knowledge/        # Vector storage & bulk indexer
│   │   ├── RAG/              # Gemini embeddings, retrieval & knowledge docs
│   │   └── repository/       # Repository architecture, hotspots & impact models
│   ├── api/                  # FastAPI routes, Pydantic schemas & dependencies
│   ├── core/                 # App configuration & logging
│   ├── db/                   # SQLAlchemy database sessions & repository models
│   ├── diff/                 # Git diff parser & file boundary isolation
│   ├── evaluation/           # Evaluation metrics & summary stats calculator
│   ├── linters/              # Flake8, PyLint, Bandit integrations
│   ├── llm/                  # Groq LLM client, prompt templates & budget tracker
│   ├── pipeline/             # Pipeline runner, orchestrator & feature aggregator
│   ├── reasoning/            # Two-phase ReviewGenerator, RootCauseEngine & Confidence
│   └── static_analysis/      # AST rules, context resolver & prioritization engine
├── tests/                    # Comprehensive unit, integration & invariant test suites
├── alembic/                  # Database migration scripts
├── requirements.txt          # Python package dependencies
├── .env.example              # Environment variables template
└── README.md                 # Service architecture & documentation
```
