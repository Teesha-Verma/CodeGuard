# CodeGuard AI

CodeGuard is an advanced, production-grade hybrid AI code review engine. It combines deterministic static analysis (AST parsing, Tree-sitter, Radon, linters) with grounded Large Language Model (LLM) reasoning to detect bugs, explain root causes, and suggest actionable fixes in Pull Requests.

## Architecture
See [docs/architecture.md](docs/architecture.md) for a detailed breakdown of the pipeline orchestrator, static analysis tools, and LLM reasoning agents.

## Quickstart

### Prerequisites
- Docker & Docker Compose
- Google Gemini API Key (`LLM_API_KEY`)

### Setup
1. Clone the repository
2. Copy `.env.example` to `.env` and fill in your keys:
   ```bash
   cp backend/.env.example backend/.env
   ```
3. Start the services using Docker Compose:
   ```bash
   cd backend
   docker-compose up -d
   ```

### API Endpoints
- `POST /review/pr`: Submits a GitHub Pull Request for analysis.
- `POST /review/snippet`: Analyzes a raw code snippet for rapid testing.

## Features
- **Deterministic Grounding**: AST extraction and control-flow analysis ground the LLM, reducing hallucinations.
- **Provider-Agnostic LLM**: Built-in support for Gemini 2.0 Flash (default) with abstractions for OpenAI and other models.
- **Observability**: Structured JSON logging and pipeline trace tracking.
- **Actionable Fixes**: Provides minimal patch suggestions alongside root-cause analysis.
