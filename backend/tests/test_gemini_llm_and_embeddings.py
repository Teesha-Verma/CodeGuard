"""
Unit tests for Google Gemini integration (Gemini 3.6 Flash & Gemini Embedding 2).
Covers Gemini LLM Client, Gemini Embedding Provider, Vector Store Dimension Validation,
and LLMClient reasoning layer.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.core.config import Settings, get_settings
from app.analysis.RAG.config.llm_config import GeminiConfig, LLMConfig
from app.analysis.RAG.config.settings import EmbeddingConfig, VectorStoreConfig, RAGConfig
from app.analysis.RAG.llm.gemini_client import GeminiClient
from app.analysis.RAG.llm.mock_client import MockGeminiClient
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.analysis.RAG.embeddings.mock_provider import MockEmbeddingProvider
from app.analysis.RAG.embeddings.service import EmbeddingService
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
from app.analysis.RAG.models.documents import EmbeddingDocument
from app.analysis.RAG.responses.review_schema import ReviewResponse
from app.llm.llm_client import LLMClient
from app.reasoning.root_cause_engine import RootCauseEngine
from app.agents.bug_detection_agent import BugDetectionAgent


class TestGeminiConfiguration:
    """Test Gemini settings and configuration validation."""

    def test_settings_gemini_defaults(self):
        settings = Settings()
        assert settings.LLM_PROVIDER == "gemini"
        assert settings.LLM_MODEL == "gemini-3.6-flash"
        assert settings.GEMINI_LLM_MODEL == "gemini-3.6-flash"
        assert settings.EMBEDDING_PROVIDER == "gemini"
        assert settings.EMBEDDING_MODEL == "gemini-embedding-2"
        assert settings.GEMINI_EMBEDDING_MODEL == "gemini-embedding-2"
        assert settings.EMBEDDING_DIMENSION == 768

    def test_settings_validation_missing_key(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("LLM_API_KEY", "")
        settings = Settings(GEMINI_API_KEY="", LLM_API_KEY="")
        with pytest.raises(ValueError) as exc_info:
            settings.validate_gemini_credentials()
        assert "Gemini API key is required" in str(exc_info.value)
        # Ensure error message does NOT expose any secrets
        assert "AIza" not in str(exc_info.value)

    def test_rag_config_gemini_env(self, monkeypatch):
        monkeypatch.setenv("RAG_EMBEDDING_PROVIDER", "gemini")
        monkeypatch.setenv("RAG_EMBEDDING_MODEL", "gemini-embedding-2")
        monkeypatch.setenv("EMBEDDING_DIMENSION", "768")
        rag_conf = RAGConfig.from_env()
        assert rag_conf.embedding.provider == "gemini"
        assert rag_conf.embedding.model == "gemini-embedding-2"
        assert rag_conf.embedding.dimension == 768


class TestGeminiLLMClient:
    """Test GeminiClient execution, sampling parameter constraints, and error handling."""

    def test_gemini_client_provider_name(self):
        client = GeminiClient(api_key="mock_key", model="gemini-3.6-flash")
        assert client.provider_name == "gemini"
        assert client.model == "gemini-3.6-flash"

    def test_gemini_client_missing_key_error(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("LLM_API_KEY", "")
        client = GeminiClient(api_key="", model="gemini-3.6-flash")
        with pytest.raises(ValueError) as excinfo:
            client._get_client()
        assert "Gemini API key is required" in str(excinfo.value)

    def test_gemini_client_structured_generation_omits_deprecated_params(self):
        client = GeminiClient(api_key="test_valid_key", model="gemini-3.6-flash")

        mock_response = MagicMock()
        mock_response.text = '{"review_summary": "Test review", "overall_severity": "low", "findings": [], "evidence_summary": "Clean", "reasoning_trace": "None", "confidence": 0.9, "priority": "low", "remediation_summary": "", "code_suggestions": [], "references": [], "review_metadata": {}}'

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value = mock_response
        client._client = mock_genai_client

        res = client.generate_review(prompt="Review auth flow")
        assert isinstance(res, ReviewResponse)
        assert res.review_summary == "Test review"

        # Verify generate_content call arguments
        mock_genai_client.models.generate_content.assert_called_once()
        call_kwargs = mock_genai_client.models.generate_content.call_args[1]
        assert call_kwargs["model"] == "gemini-3.6-flash"
        gen_config = call_kwargs.get("config")
        if gen_config is not None:
            # Crucial: temperature, top_p, top_k should NOT be configured
            assert getattr(gen_config, "temperature", None) is None
            assert getattr(gen_config, "top_p", None) is None
            assert getattr(gen_config, "top_k", None) is None

    def test_gemini_client_raw_generation(self):
        client = GeminiClient(api_key="test_valid_key", model="gemini-3.6-flash")

        mock_response = MagicMock()
        mock_response.text = "Raw generated summary"

        mock_genai_client = MagicMock()
        mock_genai_client.models.generate_content.return_value = mock_response
        client._client = mock_genai_client

        text = client.generate_raw("Summarize PR", system_instruction="You are a code reviewer")
        assert text == "Raw generated summary"


class TestGeminiEmbeddingProvider:
    """Test GeminiEmbeddingProvider with gemini-embedding-2."""

    def test_gemini_embedding_provider_initialization(self):
        provider = GeminiEmbeddingProvider(api_key="mock_key", model="gemini-embedding-2", dimension=768)
        assert provider.model_name == "gemini-embedding-2"
        assert provider.dimension == 768

    def test_gemini_embedding_provider_mocked_calls(self):
        provider = GeminiEmbeddingProvider(api_key="test_key", model="gemini-embedding-2", dimension=768)

        mock_embedding_obj = MagicMock()
        mock_embedding_obj.values = [0.1] * 768

        mock_response = MagicMock()
        mock_response.embeddings = [mock_embedding_obj]

        mock_genai_client = MagicMock()
        mock_genai_client.models.embed_content.return_value = mock_response
        provider._client = mock_genai_client

        # Single text
        emb = provider.embed_text("Sample vulnerability description")
        assert len(emb) == 768
        assert emb[0] == 0.1

        # Batch
        batch_response = MagicMock()
        batch_response.embeddings = [mock_embedding_obj, mock_embedding_obj]
        mock_genai_client.models.embed_content.return_value = batch_response
        batch_embs = provider.embed_batch(["text 1", "text 2"])
        assert len(batch_embs) == 2
        assert len(batch_embs[0]) == 768

        # Query
        mock_genai_client.models.embed_content.return_value = mock_response
        query_emb = provider.embed_query("Search SQL injection")
        assert len(query_emb) == 768


class TestVectorStoreDimensionValidation:
    """Test in-memory vector store dimension validation."""

    def test_vector_store_correct_dimension(self):
        store = InMemoryVectorStore(dimension=768)
        doc = EmbeddingDocument(
            chunk_id="chunk_1",
            document_id="doc_1",
            content="SQL injection protection guide",
            embedding=[0.05] * 768,
            metadata={"title": "OWASP SQLi"}
        )
        added = store.add_documents([doc])
        assert added == 1
        assert store.count() == 1

        results = store.search(query_embedding=[0.05] * 768, top_k=1)
        assert len(results) == 1
        assert results[0].chunk_id == "chunk_1"

    def test_vector_store_dimension_mismatch_raises(self):
        store = InMemoryVectorStore(dimension=768)
        doc_incompatible = EmbeddingDocument(
            chunk_id="chunk_bad",
            document_id="doc_bad",
            content="Incompatible vector dimension",
            embedding=[0.1] * 128,  # Mismatch: 128 != 768
        )
        with pytest.raises(ValueError) as excinfo:
            store.add_documents([doc_incompatible])
        assert "Vector dimension mismatch" in str(excinfo.value)
        assert "768" in str(excinfo.value)
        assert "128" in str(excinfo.value)

    def test_vector_store_query_dimension_mismatch_raises(self):
        store = InMemoryVectorStore(dimension=768)
        doc = EmbeddingDocument(
            chunk_id="chunk_1",
            document_id="doc_1",
            content="Sample text",
            embedding=[0.05] * 768,
        )
        store.add_documents([doc])

        with pytest.raises(ValueError) as excinfo:
            store.search(query_embedding=[0.1] * 64, top_k=5)  # Mismatch query
        assert "Query vector dimension mismatch" in str(excinfo.value)


class TestLLMReasoningLayer:
    """Test LLMClient in app.llm and reasoning integration."""

    def test_llm_client_mock_mode(self):
        client = LLMClient(review_id="test_rev_1")
        res = client.generate_structured(
            system_prompt="You are a root cause engine.",
            user_content='{"finding": {"issue": "SQL injection", "line": 42}}'
        )
        assert res is not None
        assert "root_cause" in res
        assert "fix" in res

    def test_root_cause_engine_with_gemini_client(self):
        engine = RootCauseEngine(review_id="test_rev_2")
        finding = {
            "line": 10,
            "issue": "Use of eval() detected",
            "severity": "critical",
            "sources": ["ast"],
            "evidence": {}
        }
        context = {
            "file_path": "app/calculator.py",
            "code_context": [{"start_line": 5, "code": "def calc(inp):\n    return eval(inp)"}],
            "ast_structural_metadata": {}
        }
        explanation = engine.analyze_finding(finding, context)
        assert explanation is not None
        assert "root_cause" in explanation
        assert "fix" in explanation

    def test_bug_detection_agent_with_gemini_client(self):
        agent = BugDetectionAgent(review_id="test_rev_3")
        features = {
            "file_path": "app/auth.py",
            "changed_lines": [12],
            "dangerous_patterns": [{"line": 12, "message": "Insecure hash function used"}]
        }
        issues = agent.detect(features)
        assert len(issues) >= 1
        assert issues[0]["line"] == 12 or issues[0]["line"] == 1
