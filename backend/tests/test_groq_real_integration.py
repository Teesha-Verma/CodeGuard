"""
Real Groq LLM Integration Tests for CodeGuard V2.

Verifies that:
1. GROQ_API_KEY connects to Groq API.
2. llama-3.3-70b-versatile generates real responses.
3. LLMClient generates structured JSON and sets reasoning_source="llm".
4. RootCauseEngine produces grounded root cause analysis with reasoning_source="llm".
5. GroqClient in RAG generates valid ReviewResponse objects.
6. Fallback from llama-3.3-70b-versatile to llama-3.1-8b-instant and static reasoning works as expected.
"""

import os
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

import groq
from groq import Groq

from app.core.config import get_settings
from app.llm.llm_client import LLMClient
from app.reasoning.root_cause_engine import RootCauseEngine, ROOT_CAUSE_SYSTEM_PROMPT
from app.analysis.RAG.llm.groq_client import GroqClient
from app.analysis.RAG.responses.review_schema import ReviewResponse


@pytest.fixture(autouse=True)
def enable_real_groq_test(monkeypatch):
    """Enable real Groq test mode."""
    get_settings.cache_clear()
    settings = get_settings()
    monkeypatch.setenv("GROQ_REAL_TEST", "true")
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    if settings.GROQ_API_KEY:
        monkeypatch.setenv("GROQ_API_KEY", settings.GROQ_API_KEY)
    yield
    get_settings.cache_clear()


class TestGroqRealIntegration:
    """Test suite executing live requests against the Groq API."""

    def test_01_direct_groq_sdk_call(self):
        """Verify direct Groq API connectivity and response generation."""
        settings = get_settings()
        api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY")
        assert api_key and not api_key.startswith("your_"), "Valid GROQ_API_KEY required for integration test."

        # Use active available Groq chat model
        model_name = settings.GROQ_PRIMARY_MODEL or "openai/gpt-oss-120b"
        client = Groq(api_key=api_key, timeout=30.0)
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a code review assistant. Output JSON only."},
                {"role": "user", "content": "Explain why eval('2 + 2') is dangerous in JSON: {'hazard': '...'}"}
            ],
            model=model_name,
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=1024,
        )

        assert response.choices and len(response.choices) > 0
        content = response.choices[0].message.content
        assert content, "Groq response content must not be empty."

        parsed = json.loads(content)
        assert isinstance(parsed, dict)

    def test_02_codeguard_llm_client_structured_json(self):
        """Verify CodeGuard LLMClient produces structured JSON with reasoning_source='llm'."""
        review_id = f"test_groq_client_{uuid.uuid4().hex[:8]}"
        client = LLMClient(review_id=review_id)

        system_prompt = (
            "You are a code security analyzer. Analyze this code and return JSON with keys: "
            "'root_cause', 'trigger_condition', 'fix', 'patch', 'issue_type'."
        )
        user_content = "def execute_code(user_input):\n    eval(user_input)\n"

        result = client.generate_structured(system_prompt, user_content)
        assert result is not None
        assert isinstance(result, dict)
        assert "root_cause" in result
        assert "fix" in result
        assert result.get("reasoning_source") == "llm"

    def test_03_root_cause_engine_llm_reasoning_source(self):
        """Verify RootCauseEngine uses Groq to generate grounded explanations with reasoning_source='llm'."""
        review_id = f"test_groq_rce_{uuid.uuid4().hex[:8]}"
        engine = RootCauseEngine(review_id=review_id)

        finding = {
            "line": 2,
            "issue": "Use of unsafe eval() allows arbitrary code execution",
            "severity": "critical",
            "sources": ["ast"],
            "evidence": {
                "ast_rule": "eval_detection",
                "details": "Dynamic execution of untrusted input via built-in eval()"
            }
        }
        aggregated_context = {
            "file_path": "security/eval_service.py",
            "code_context": [
                {
                    "start_line": 1,
                    "code": "def process_query(payload):\n    return eval(payload)\n"
                }
            ],
            "ast_structural_metadata": {
                "functions": [{"name": "process_query", "start_line": 1, "end_line": 2}],
                "ast_rules_findings": [{"line": 2, "rule_name": "eval_detection", "message": "eval call detected"}]
            },
            "retrieved_knowledge": "Rule OWASP-A03: Do not evaluate dynamic string expressions. Use ast.literal_eval."
        }

        explanation = engine.analyze_finding(finding, aggregated_context)
        assert explanation is not None
        assert explanation.get("reasoning_source") == "llm"
        assert "root_cause" in explanation
        assert "fix" in explanation

    def test_04_rag_groq_client_review_generation(self):
        """Verify GroqClient in RAG produces a validated ReviewResponse."""
        review_id = f"test_rag_groq_{uuid.uuid4().hex[:8]}"
        client = GroqClient(review_id=review_id)

        prompt = "Review this Python code with RAG context:\nCode: os.system(f'rm -rf {user_dir}')\nContext: Rule CWE-78 OS Command Injection"
        review_res = client.generate_review(prompt=prompt)

        assert isinstance(review_res, ReviewResponse)
        assert review_res.review_summary
        assert review_res.overall_severity in ("low", "medium", "high", "critical")

    def test_05_groq_rate_limit_fallback_cascade(self, monkeypatch):
        """Verify graceful fallback from primary model to fallback model on rate limit."""
        monkeypatch.delenv("GROQ_REAL_TEST", raising=False)
        monkeypatch.delenv("GEMINI_REAL_TEST", raising=False)

        review_id = f"test_fallback_{uuid.uuid4().hex[:8]}"
        client = LLMClient(review_id=review_id)
        primary_model = client.model

        call_models = []

        def mock_create(*args, **kwargs):
            model = kwargs.get("model")
            call_models.append(model)
            if model == primary_model:
                raise Exception("429 rate_limit_exceeded: Rate limit reached for model")
            # Fallback model succeeds
            mock_choice = MagicMock()
            mock_choice.message.content = json.dumps({
                "root_cause": "Unsafe command execution.",
                "trigger_condition": "User input concatenated to shell command.",
                "fix": "Use subprocess.run with argument list."
            })
            mock_resp = MagicMock()
            mock_resp.choices = [mock_choice]
            return mock_resp

        with patch("groq.resources.chat.completions.Completions.create", side_effect=mock_create):
            result = client.generate_structured(f"unique_system_prompt_{uuid.uuid4().hex}", "unique user content")
            assert result is not None
            assert result.get("reasoning_source") == "llm"
            assert primary_model in call_models
            assert len(call_models) >= 2

    def test_06_all_groq_failure_fallback_to_static(self, monkeypatch):
        """Verify graceful degradation to static analysis when all Groq models fail."""
        monkeypatch.delenv("GROQ_REAL_TEST", raising=False)
        monkeypatch.delenv("GEMINI_REAL_TEST", raising=False)

        review_id = f"test_all_fail_{uuid.uuid4().hex[:8]}"
        client = LLMClient(review_id=review_id)

        with patch("groq.resources.chat.completions.Completions.create", side_effect=Exception("500 Internal Server Error")):
            result = client.generate_structured(f"all_fail_sys_{uuid.uuid4().hex}", f"all_fail_usr_{uuid.uuid4().hex}")
            # When client returns None, RootCauseEngine/ReviewGenerator falls back to static analysis
            assert result is None
