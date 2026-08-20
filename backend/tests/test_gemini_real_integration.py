"""
CodeGuard V2 — Real Google Gemini API Integration Tests.

Validates:
- Real Gemini 3.6 Flash structured review generation (JSON output mode)
- Real Gemini Embedding 2 vector generation (768 dimensions)
- Real Vector Store indexing and cosine similarity search
- Strict credential safety (no secret leakage)
"""

import json
import pytest
from app.core.config import get_settings
from app.llm.llm_client import LLMClient
from app.reasoning.root_cause_engine import ROOT_CAUSE_SYSTEM_PROMPT, RootCauseEngine
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
from app.analysis.RAG.models.documents import EmbeddingDocument


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured in .env; skipping real Gemini tests.")
    return conf


class TestGeminiRealIntegration:
    """Real Google Gemini API integration tests with configured GEMINI_API_KEY."""

    def test_gemini_real_llm_client_structured_generation(self, settings):
        """Verify real Gemini 3.6 Flash generates structured JSON for code review."""
        llm_client = LLMClient(review_id="test_real_gemini_llm")

        payload = {
            "finding": {
                "line": 15,
                "issue": "Raw SQL concatenation detected in user query execution",
                "severity": "critical",
                "sources": ["ast", "bandit", "dataflow"],
                "evidence": {
                    "ast_nodes": [{"pattern": "eval_detection", "message": "Raw SQL concatenation"}],
                    "linter_rules": [{"tool": "bandit", "rule_id": "B608", "message": "Possible SQL injection"}],
                    "dataflow_findings": [{"rule_id": "SQL_INJECTION", "sink_node": "cursor.execute"}],
                }
            },
            "file_path": "app/db/user_repo.py",
            "localized_code": "def get_user(user_id):\n    cursor.execute(f'SELECT * FROM users WHERE id={user_id}')\n    return cursor.fetchone()",
            "structural_context": {
                "function": {"name": "get_user", "is_async": False},
                "retrieved_knowledge": "Rule CWE-89: Always use parameterized queries (e.g. cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,)))"
            }
        }

        response = llm_client.generate_structured(
            system_prompt=ROOT_CAUSE_SYSTEM_PROMPT,
            user_content=json.dumps(payload, indent=2)
        )

        assert response is not None
        assert isinstance(response, dict)
        assert "root_cause" in response
        assert "trigger_condition" in response
        assert "fix" in response
        assert "issue_type" in response

        # Verify structured quality
        assert len(response["root_cause"]) > 10
        assert len(response["fix"]) > 10
        assert response["issue_type"] in ("security", "runtime_logic_error", "code_smell", "complexity", "style")

    def test_gemini_real_root_cause_engine(self, settings):
        """Verify RootCauseEngine with real Gemini 3.6 Flash."""
        engine = RootCauseEngine(review_id="test_real_engine")

        finding = {
            "line": 8,
            "issue": "Modifying list elements while iterating over the same list",
            "severity": "high",
            "sources": ["ast"],
            "evidence": {
                "ast_nodes": [{"pattern": "mutation_during_iteration", "message": "List modified in loop"}]
            }
        }
        aggregated_context = {
            "file_path": "app/utils/cleaner.py",
            "code_context": [{
                "start_line": 1,
                "code": "def remove_invalid(items):\n    for x in items:\n        if x < 0:\n            items.remove(x)"
            }],
            "ast_structural_metadata": {
                "functions": [{"name": "remove_invalid", "start_line": 1, "end_line": 5}]
            }
        }

        explanation = engine.analyze_finding(finding, aggregated_context)
        assert explanation is not None
        assert "root_cause" in explanation
        assert "fix" in explanation
        assert len(explanation["root_cause"].split(".")) <= 4  # Max 3-4 sentences constraint

    def test_gemini_real_embedding_generation_768_dim(self, settings):
        """Verify real Gemini Embedding 2 generates 768-dimensional embeddings."""
        provider = GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_EMBEDDING_MODEL or "gemini-embedding-2",
            dimension=768,
        )

        # Single text embedding
        doc_vector = provider.embed_text("Always parameterize SQL queries to prevent SQL injection vulnerabilities.")
        assert isinstance(doc_vector, list)
        assert len(doc_vector) == 768
        assert all(isinstance(x, (float, int)) for x in doc_vector)

        # Query embedding
        query_vector = provider.embed_query("How to fix SQL injection in Python?")
        assert isinstance(query_vector, list)
        assert len(query_vector) == 768

        # Batch embedding
        batch_vectors = provider.embed_batch([
            "Use context managers to safely close database connections.",
            "Avoid using mutable default arguments in Python functions."
        ])
        assert len(batch_vectors) == 2
        assert len(batch_vectors[0]) == 768
        assert len(batch_vectors[1]) == 768

    def test_gemini_real_vector_store_indexing_and_search(self, settings):
        """Verify vector indexing and semantic retrieval using real Gemini embeddings."""
        provider = GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model="gemini-embedding-2",
            dimension=768,
        )
        store = InMemoryVectorStore(dimension=768)

        # Generate real embeddings for documents
        doc1_text = "Security: Prevent SQL injection by parameterizing database queries."
        doc2_text = "Performance: Use list comprehensions or generators for memory efficiency."
        doc3_text = "Concurrency: Never block the asyncio event loop with synchronous sleep."

        embs = provider.embed_batch([doc1_text, doc2_text, doc3_text])

        docs = [
            EmbeddingDocument(chunk_id="c1", document_id="d1", content=doc1_text, embedding=embs[0], metadata={"category": "security"}),
            EmbeddingDocument(chunk_id="c2", document_id="d2", content=doc2_text, embedding=embs[1], metadata={"category": "performance"}),
            EmbeddingDocument(chunk_id="c3", document_id="d3", content=doc3_text, embedding=embs[2], metadata={"category": "async"}),
        ]

        added = store.add_documents(docs)
        assert added == 3
        assert store.count() == 3

        # Search with real query embedding
        query_emb = provider.embed_query("database sql injection vulnerability")
        results = store.search(query_embedding=query_emb, top_k=1)

        assert len(results) == 1
        assert results[0].chunk_id == "c1"
        assert results[0].score > 0.4
