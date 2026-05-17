# CodeGuard Architecture

CodeGuard is built on a modular pipeline designed to extract structural context before querying the LLM, ensuring highly grounded and accurate code reviews.

## High-Level Flow

1. **Input Preprocessing**: A request (PR or snippet) is received via FastAPI.
2. **Diff Parsing**: `DiffParser` and `ContextBuilder` extract changed lines and surrounding code context.
3. **Static Analysis Layer**:
   - `PythonASTParser` & `TreeSitterParser`: Extract function and class structures.
   - `ComplexityAnalyzer`: Calculates Cyclomatic Complexity via Radon.
   - `ScopeTracker` & `ControlFlowAnalyzer`: Trace variable mutations and execution paths.
   - `PatternDetector`: Flags known anti-patterns (e.g., mutable defaults).
4. **Linter Integration**: Wrappers for `pylint`, `flake8`, and `bandit` run synchronously.
5. **Feature Aggregation**: The `FeatureAggregator` merges all signals into a unified context payload.
6. **LLM Reasoning Layer**:
   - **Bug Detection Agent**: Uses the context payload to flag high-confidence bugs.
   - **Root Cause Agent**: Explains the underlying problem for each bug.
   - **Fix Suggestion Agent**: Proposes a minimal, actionable code patch.
7. **Storage & Eval**: Results are tracked in SQLite/PostgreSQL, alongside pipeline execution traces.

## Directory Structure
- `app/api/`: FastAPI routes and Pydantic schemas.
- `app/core/`: Configuration, constants, and structured logging.
- `app/diff/`: Git diff parsing and context extraction.
- `app/static_analysis/`: AST and semantic analysis modules.
- `app/linters/`: Deterministic linter wrappers.
- `app/llm/`: Prompts, parsers, and the provider-agnostic `LLMClient`.
- `app/agents/`: Specific LLM agents for detection, root cause, and fixes.
- `app/pipeline/`: Orchestrator that ties everything together.
- `app/db/`: SQLAlchemy ORM models and repositories.
