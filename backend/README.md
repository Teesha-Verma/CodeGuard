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

## 2. PR-Scoped Analysis & Context Isolation

CodeGuard V2 enforces strict **PR-scoped analysis** to optimize review latency, static analysis overhead, and LLM/RAG token consumption:

```
GitHub Pull Request (Authoritative Changed Files)
                 │
                 ▼
      PR_ANALYSIS_SCOPE: Exact PR Files
       (added, modified, renamed new-path)
      (removed files skipped from active AST)
                 │
        ┌────────┴────────────────────────┐
        ▼                                 ▼
Primary PR Static Analysis       Need Local Context?
 (AST, Flake8, PyLint, Bandit)             │
        │                                 ▼
        │                    SUPPORTING_CONTEXT_SCOPE:
        │                    Targeted Local Imports & Symbols
        │                    (bounded to referenced modules only)
        │                                 │
        ▼                                 ▼
   PR-Scoped Findings ◄── Filter ── Non-PR Repository Code Excluded
        │                 (finding.file_path ∈ PR_CHANGED_FILES)
        ▼
PR Review Report & LLM Reasoning
```

### Key Architectural Principles:
1. **Exact Path Matching**: Review scope is governed strictly by normalized repository-relative paths (e.g. `src/utils/parser.py`). Basename, suffix, or fuzzy matching (`tests/utils/parser.py`, `legacy/parser.py`) is strictly eliminated.
2. **File Status Semantics**:
   - `added` / `modified`: Analyzed as active primary files.
   - `renamed`: Analyzed using the new destination path.
   - `removed`: Explicitly skipped from source AST analysis to prevent missing file errors.
3. **Primary vs. Supporting Context Scope**:
   - `PR_ANALYSIS_SCOPE`: Only files directly touched in the PR receive full static analysis (AST, CFG, linters, taint analysis).
   - `SUPPORTING_CONTEXT_SCOPE`: Bounded local dependencies (imported modules, base classes, called functions) are inspected solely to resolve cross-file symbol context for primary files.
   - Repository-wide files are **never** mass-analyzed, and issues in supporting context are **never** reported as PR findings.
4. **Hard Finding Filtering**: Before entering `ReviewGenerator`, every finding is validated against `finding.file_path ∈ PR_CHANGED_FILES`. Any finding outside the PR change set is dropped from the report.
5. **PR-Scoped Style Warnings**: Linters (Flake8, PyLint) only report violations on the PR's changed files, eliminating noisy repository-wide formatting warnings.
6. **Token & Performance Optimization**: RAG vector retrieval and LLM context construction only include PR changed hunks and localized supporting symbols (capped at ±50 lines), drastically reducing Groq and Gemini token expenditure.

---

## 3. Secret Protection & Repository Hygiene

To safeguard credentials and prevent accidental data leakage:
1. **Strict Git Ignore Rules**:
   - `.env`, `.env.*`, `**/.env`, `**/.env.*`, `*.key`, `*.pem`, `*.crt`, `*.pfx` are globally ignored across all directories.
   - `.env.example` and `**/.env.example` are explicitly tracked and contain **placeholders only**.
2. **Never Commit Secrets**: Real credentials (API keys, connection strings, auth tokens) must reside exclusively in uncommitted `.env` files or secure environment variables.
3. **Secret-Safe Logging**: The logging system employs centralized regex redaction (`mask_secrets`) to sanitize Groq keys, Gemini keys, GitHub tokens, Bearer authorization headers, and database connection strings before writing to console or disk.
4. **Sanitized Error Responses**: API 500 error handlers sanitize exception messages and tracebacks, preventing database URLs or secrets from leaking to clients.
5. **Credential Rotation Notice**:
   > [!WARNING]
   > Historical Git commit `48ad88de8516818443ca99ea2882c5c91daaf70e` committed an API key to `backend/.env.example`. Any credentials committed in historical commits must be immediately revoked and rotated at the provider dashboard. Git ignore alone does not revoke previously committed secrets.

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

### 2.2. Multi-Provider LLM Reasoning & Fallback Architecture

CodeGuard V2 implements a robust two-level multi-provider LLM reasoning architecture:

```
                  Structured LLM Request
                            │
                            ▼
              Shared Review Budget Check (≤25)
                            │
                            ▼
             Prompt Deduplication Cache Check
                            │
                            ▼
           ┌───────────────────────────────────┐
           │        ProviderRouter             │
           │  [Level 1: Provider Selection]    │
           └────────────────┬──────────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
┌───────────────────────────────┐   ┌───────────────────────────────┐
│ Primary Provider: Groq        │   │ Fallback Provider: Gemini     │
│ [Level 2: Model Cascade]      │   │ [Level 2: Model Cascade]      │
│ 1. Primary: openai/gpt-oss-120b│  │ 1. Primary: gemini-3.5-flash │
│ 2. Fallback: qwen/qwen3.8-27b │   │ 2. Fallback: gemini-3.5-flash-lite
│ 3. Fallback: llama-3.3-70b    │   │ 3. Fallback: gemini-3.6-flash │
│ 4. Fallback: llama-3.1-8b     │   └───────────────┬───────────────┘
└───────────────┬───────────────┘                   │
                │ Quota / Model Exhausted           │
                └───────────────►───────────────────┘
                                                    │ Both Providers Exhausted
                                                    ▼
                                    Deterministic Static Analysis
                                    (Zero Pipeline Failures)
```

- **Two-Level Fallback**:
  - **Level 1 (Provider Fallover)**: Groq acts as primary LLM. If Groq experiences rate limits, daily token quota (TPD) exhaustion, service outages, or model unavailability, the pipeline transparently fails over to Google Gemini LLM reasoning.
  - **Level 2 (Model Cascade within Provider)**: Each provider cascades through ordered candidate models before giving up to the next provider.
- **Intelligent Error Discrimination**:
  - **Daily Quota / TPD Exhaustion**: Immediately switches with **zero wasteful retries**, permanently blacklisting the exhausted model/provider for the remainder of that review.
  - **Temporary RPM Limits**: Applies bounded exponential backoff with jitter before retrying.
- **Review-Aware Provider State**: Once a provider hits daily quota in a review, all subsequent findings in that review automatically bypass the exhausted provider without thrashing.
- **Shared Request Budget**: Fallback requests replace the failed request; they never double-count against the review's `max_requests` limit.
- **Finding-Level Traceability**: Every reasoning output records `reasoning_source: "llm"`, `llm_provider: "groq"|"gemini"`, and `llm_model: string` in both memory schemas and persisted database evidence.
- **Per-Review Accounting**: `ReviewLLMTracker` records per-provider metrics (requests, successes, failures, rate limits, quota exhaustions, fallbacks triggered, token usage, and latency).

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

# Run multi-provider LLM failover and quota test suite
pytest tests/test_multi_provider_llm.py tests/test_llm_quota_and_fallback.py -v

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
