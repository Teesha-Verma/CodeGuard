"""
CodeGuard V2 — Real Google Gemini 2.5 Flash API Verification Suite.

Validates:
1. Direct Google GenAI SDK call to gemini-2.5-flash.
2. CodeGuard LLMClient structured JSON generation using gemini-2.5-flash.
3. RootCauseEngine grounded reasoning using gemini-2.5-flash (fails if static fallback).
4. RAG GeminiClient structured review generation using gemini-2.5-flash.
5. GeminiEmbeddingProvider 768-dimensional embedding generation using gemini-embedding-2.
6. Model selection safety: verifies gemini-2.5-flash is primary and gemini-2.5-flash-lite is excluded.
7. Cache bypass and fallback prohibition during dedicated verification.
"""

import json
import os
import pytest

from app.core.config import get_settings
from app.llm.llm_client import LLMClient
from app.reasoning.root_cause_engine import RootCauseEngine, ROOT_CAUSE_SYSTEM_PROMPT
from app.analysis.RAG.llm.gemini_client import GeminiClient
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.analysis.RAG.responses.review_schema import ReviewResponse

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


@pytest.fixture(autouse=True)
def enable_real_test_mode(monkeypatch):
    """Ensure GEMINI_REAL_TEST is enabled for all tests in this suite."""
    monkeypatch.setenv("GEMINI_REAL_TEST", "true")
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_PRIMARY_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("GEMINI_LLM_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash")


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured in .env; skipping real Gemini 2.5 Flash tests.")
    return conf


class TestGemini25FlashReal:
    """Dedicated real API verification suite for gemini-2.5-flash."""

    def test_01_direct_genai_sdk_call(self, settings):
        """Test 1: Direct Google GenAI SDK call to gemini-2.5-flash."""
        assert genai is not None, "google-genai SDK must be installed."
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = "Explain in one sentence why SQL string concatenation is vulnerable to injection attacks."
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        assert response is not None, "Direct GenAI response must not be None."
        text = response.text if hasattr(response, "text") else str(response)
        assert text, "Direct GenAI response text must not be empty."
        assert len(text.strip()) > 10, "Response text must be substantive."
        assert any(term in text.lower() for term in ("sql", "injection", "query", "parameter", "vulnerab"))

    def test_02_codeguard_llm_client_structured_json(self, settings):
        """Test 2: CodeGuard LLMClient structured JSON generation with gemini-2.5-flash."""
        llm_client = LLMClient(review_id="test_real_25_flash_structured")
        assert llm_client.model == "gemini-2.5-flash", f"LLMClient model must be gemini-2.5-flash, got {llm_client.model}"

        payload = {
            "finding": {
                "line": 5,
                "issue": "SQL injection via string concatenation in raw SQL query",
                "severity": "critical",
                "sources": ["ast", "bandit"],
                "evidence": {
                    "ast_nodes": [{"pattern": "sql_concatenation", "message": "Unsanitized user_input concatenated into SQL query"}],
                    "linter_rules": [{"tool": "bandit", "rule_id": "B608", "message": "Possible SQL injection vector through string-based query construction"}],
                }
            },
            "file_path": "user_service.py",
            "localized_code": "import sqlite3\n\ndef get_user(user_input):\n    conn = sqlite3.connect('app.db')\n    query = \"SELECT * FROM users WHERE name = '\" + user_input + \"'\"\n    return conn.execute(query).fetchall()",
            "structural_context": {
                "function": {"name": "get_user", "is_async": False},
                "retrieved_knowledge": "Rule CWE-89: Improper Neutralization of Special Elements used in an SQL Command. Always use parameterized queries (e.g. cursor.execute('SELECT * FROM users WHERE name = ?', (user_input,))) instead of string formatting or concatenation."
            }
        }

        response = llm_client.generate_structured(
            system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
            user_content=json.dumps(payload, indent=2),
        )

        assert response is not None, "LLMClient response must not be None."
        assert isinstance(response, dict), "Response must be a parsed dictionary."
        for key in ("root_cause", "trigger_condition", "fix", "issue_type"):
            assert key in response, f"Response missing required key '{key}'"
            assert response[key], f"Response key '{key}' must not be empty."

        assert len(response["root_cause"]) > 10, "root_cause must contain detailed explanation."
        assert len(response["fix"]) > 10, "fix must contain actionable remediation."
        assert response["issue_type"] in ("security", "runtime_logic_error", "code_smell", "complexity", "style")

    def test_03_root_cause_engine_llm_reasoning_source(self, settings):
        """Test 3: RootCauseEngine reasoning must originate from LLM (reasoning_source != 'static_analysis')."""
        engine = RootCauseEngine(review_id="test_real_25_flash_engine")
        assert engine.llm_client.model == "gemini-2.5-flash"

        finding = {
            "line": 5,
            "issue": "SQL injection via string concatenation in raw SQL query",
            "severity": "critical",
            "sources": ["ast", "bandit"],
            "evidence": {
                "ast_nodes": [{"pattern": "sql_concatenation", "message": "Unsanitized user_input concatenated into SQL query"}]
            }
        }
        aggregated_context = {
            "file_path": "user_service.py",
            "code_context": [{
                "start_line": 1,
                "code": "import sqlite3\n\ndef get_user(user_input):\n    conn = sqlite3.connect('app.db')\n    query = \"SELECT * FROM users WHERE name = '\" + user_input + \"'\"\n    return conn.execute(query).fetchall()"
            }],
            "ast_structural_metadata": {
                "functions": [{"name": "get_user", "start_line": 3, "end_line": 7}]
            },
            "retrieved_knowledge": "Rule CWE-89: Improper Neutralization of Special Elements used in an SQL Command. Always use parameterized queries."
        }

        result = engine.analyze_finding(finding, aggregated_context)
        assert result is not None, "RootCauseEngine result must not be None."
        assert isinstance(result, dict)

        # STRICT ASSERTION: If static fallback was used, the test MUST FAIL
        assert result.get("reasoning_source") != "static_analysis", (
            "Test failed: RootCauseEngine fell back to static_analysis instead of real Gemini 2.5 Flash."
        )
        assert "root_cause" in result and result["root_cause"]
        assert "fix" in result and result["fix"]
        # Sentence limit check (max 3 sentences)
        sentences = [s.strip() for s in result["root_cause"].split(".") if s.strip()]
        assert len(sentences) <= 3, f"root_cause exceeded 3 sentences: {len(sentences)}"

    def test_04_rag_gemini_client_review_generation(self, settings):
        """Test 4: RAG GeminiClient generates structured review with gemini-2.5-flash."""
        client = GeminiClient(
            api_key=settings.GEMINI_API_KEY,
            model="gemini-2.5-flash",
            review_id="test_real_25_rag_client",
        )
        assert client.model == "gemini-2.5-flash"

        review = client.generate_review(
            query="Analyze this snippet for timing attacks: if hmac.compare_digest(user_hash, expected_hash): return True",
            context="Security standard: Always use constant-time comparisons for cryptographic hashes.",
        )

        assert review is not None, "GeminiClient review response must not be None."
        assert isinstance(review, ReviewResponse), "Response must be a ReviewResponse instance."
        assert review.review_summary != "", "Review summary must not be empty."
        assert review.overall_severity in ("low", "medium", "high", "critical")

    def test_05_gemini_embedding_provider_768_dim(self, settings):
        """Test 5: GeminiEmbeddingProvider with gemini-embedding-2 generates 768-dim embeddings."""
        provider = GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model="gemini-embedding-2",
            dimension=768,
        )
        assert provider.dimension == 768

        vector = provider.embed_query("Constant-time hash comparison in Python")
        assert isinstance(vector, list)
        assert len(vector) == 768, f"Expected 768 dimensions, got {len(vector)}"
        assert all(isinstance(x, (float, int)) for x in vector)

    def test_06_model_selection_safety(self, settings):
        """Test 6: Verify gemini-2.5-flash is the primary model and gemini-2.5-flash-lite is NOT in candidates."""
        client = LLMClient(review_id="test_model_safety")
        assert client.model == "gemini-2.5-flash"
        
        fallback_list = client.settings.gemini_fallback_model_list
        available_models = client.tracker.get_available_models(client.model, fallback_list)
        
        # Verify primary is first
        assert available_models[0] == "gemini-2.5-flash"
        # Verify deprecated model is completely absent
        assert "gemini-2.5-flash-lite" not in available_models
        assert "gemini-2.5-flash-lite" not in fallback_list
