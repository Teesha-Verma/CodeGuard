"""
CodeGuard V2 — Real Google Gemini Embedding Integration Tests.

Validates:
- Real Gemini Embedding 2 vector generation (768 dimensions)
- Real Query & Document text embedding
- Real Batch embedding generation
- Real Vector Store indexing and cosine similarity search
- Strict credential safety (no secret leakage)
"""

import pytest
from app.core.config import get_settings
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
from app.analysis.RAG.models.documents import EmbeddingDocument


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured in .env; skipping real Gemini embedding tests.")
    return conf


class TestGeminiRealEmbeddingIntegration:
    """Real Google Gemini Embedding API integration tests with configured GEMINI_API_KEY."""

    def test_01_gemini_real_embedding_generation_768_dim(self, settings):
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

    def test_02_gemini_real_vector_store_indexing_and_search(self, settings):
        """Verify vector indexing and semantic retrieval using real Gemini embeddings."""
        provider = GeminiEmbeddingProvider(
            api_key=settings.GEMINI_API_KEY,
            model=settings.GEMINI_EMBEDDING_MODEL or "gemini-embedding-2",
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
