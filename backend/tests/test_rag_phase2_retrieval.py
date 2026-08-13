"""Unit tests for Phase 2: Retrieval Engine & Context Intelligence Layer in app.analysis.RAG."""

import os
import pytest

from app.analysis.RAG.config.settings import RAGConfig
from app.analysis.RAG.context.base import RetrievalContextSignal
from app.analysis.RAG.context.ast_provider import ASTContextProvider
from app.analysis.RAG.context.cfg_provider import CFGContextProvider
from app.analysis.RAG.context.call_graph_provider import CallGraphContextProvider
from app.analysis.RAG.context.linter_provider import LinterContextProvider
from app.analysis.RAG.context.data_flow_adapter import DataFlowAdapter
from app.analysis.RAG.context.repo_intelligence_adapter import RepoIntelligenceAdapter
from app.analysis.RAG.query_builder.builder import QueryBuilder, RetrievalQuery
from app.analysis.RAG.filters.filter_engine import MetadataFilterEngine
from app.analysis.RAG.search.result import DetailedSearchResult
from app.analysis.RAG.reranker.weighted_reranker import WeightedReranker
from app.analysis.RAG.retrieval.engine import RetrievalEngine
from app.analysis.RAG.context.assembler import ContextAssembler, AssembledContext
from app.analysis.RAG.cache.retrieval_cache import RetrievalCache
from app.analysis.RAG.embeddings.mock_provider import MockEmbeddingProvider
from app.analysis.RAG.embeddings.service import EmbeddingService
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
from app.analysis.RAG.models.documents import EmbeddingDocument


class TestContextProvidersAndAdapters:
    """Test all Context Providers and Adapters."""

    def test_ast_context_provider(self):
        provider = ASTContextProvider()
        raw_ast_output = {
            "node_types": ["FunctionDef", "Call"],
            "function_names": ["execute_query"],
            "dangerous_calls": ["eval", "exec"],
            "vulnerability_types": ["code_injection"],
            "file_path": "app/db/query.py",
        }
        signal = provider.extract_signal(raw_ast_output)
        assert signal.signal_type == "ast"
        assert "FunctionDef" in signal.query_tokens
        assert "code_injection" in signal.vulnerability_types
        assert signal.file_path == "app/db/query.py"

    def test_cfg_context_provider(self):
        provider = CFGContextProvider()
        raw_cfg = {
            "unreachable_blocks": 2,
            "cyclomatic_complexity": 12,
            "branch_conditions": ["if user_input is None"],
        }
        signal = provider.extract_signal(raw_cfg)
        assert signal.signal_type == "cfg"
        assert "cyclomatic_complexity:12" in signal.query_tokens

    def test_call_graph_provider(self):
        provider = CallGraphContextProvider()
        raw_cg = {
            "caller": "api_endpoint",
            "callee": "raw_sql_executor",
            "call_depth": 3,
        }
        signal = provider.extract_signal(raw_cg)
        assert signal.signal_type == "call_graph"
        assert "raw_sql_executor" in signal.query_tokens

    def test_linter_provider(self):
        provider = LinterContextProvider()
        raw_linter = [
            {"code": "B101", "message": "Assert used", "line": 42},
            {"code": "E501", "message": "Line too long", "line": 10},
        ]
        signal = provider.extract_signal(raw_linter)
        assert signal.signal_type == "linter"
        assert "B101" in signal.query_tokens

    def test_data_flow_adapter(self):
        adapter = DataFlowAdapter()
        raw_dataflow = {
            "source": "request.args.get('input')",
            "sink": "cursor.execute(query)",
            "path": ["request", "input", "query", "execute"],
            "taint_type": "sql_injection",
        }
        signal = adapter.adapt(raw_dataflow)
        assert signal.signal_type == "data_flow"
        assert "sql_injection" in signal.vulnerability_types
        assert "cursor.execute(query)" in signal.query_tokens

    def test_repo_intelligence_adapter(self):
        adapter = RepoIntelligenceAdapter()
        raw_repo_intel = {
            "primary_language": "python",
            "framework": "fastapi",
            "orm": "sqlalchemy",
            "database": "postgresql",
            "architecture_style": "clean_architecture",
        }
        signal = adapter.adapt(raw_repo_intel)
        assert signal.signal_type == "repo_intel"
        assert signal.languages == ["python"]
        assert signal.frameworks == ["fastapi"]
        assert signal.databases == ["postgresql"]
        assert signal.orms == ["sqlalchemy"]


class TestQueryBuilderAndFilters:
    """Test QueryBuilder and MetadataFilterEngine."""

    def test_query_builder(self):
        ast_signal = ASTContextProvider().extract_signal({
            "vulnerability_types": ["sql_injection"],
            "function_names": ["execute"],
        })
        repo_signal = RepoIntelligenceAdapter().adapt({
            "primary_language": "python",
            "framework": "fastapi",
            "orm": "sqlalchemy",
            "database": "postgresql",
        })

        builder = QueryBuilder()
        query = builder.build_query([ast_signal, repo_signal])
        assert isinstance(query, RetrievalQuery)
        assert "fastapi" in query.raw_query_string.lower()
        assert "sql_injection" in query.raw_query_string.lower()
        assert "python" in query.filters.get("languages", [])

    def test_metadata_filter_engine(self):
        filter_engine = MetadataFilterEngine()
        metadatas = [
            {"category": "security", "languages": ["python"], "frameworks": ["fastapi"]},
            {"category": "python", "languages": ["python"], "frameworks": ["django"]},
            {"category": "security", "languages": ["java"], "frameworks": ["spring_boot"]},
        ]
        criteria = {"category": "security", "languages": ["python"]}
        matches = filter_engine.apply_pre_filters(criteria, metadatas)
        assert matches == [True, False, False]


class TestRerankerAndScorer:
    """Test WeightedReranker and scoring helpers."""

    def test_weighted_reranker(self):
        reranker = WeightedReranker(framework_boost=1.5, security_boost=1.2)
        results = [
            DetailedSearchResult(
                chunk_id="c1",
                document_id="d1",
                title="SQL Injection in FastAPI",
                content="SQL injection details for FastAPI apps using SQLAlchemy.",
                source_path="/kb/sql_inj.md",
                similarity_score=0.8,
                metadata_score=0.7,
                matched_frameworks=["fastapi"],
                matched_languages=["python"],
                matched_concepts=["sql_injection"],
                confidence=0.85,
            ),
            DetailedSearchResult(
                chunk_id="c2",
                document_id="d2",
                title="Generic Code Formatting",
                content="Formatting code in Python using PEP 8.",
                source_path="/kb/pep8.md",
                similarity_score=0.6,
                metadata_score=0.4,
                matched_frameworks=[],
                matched_languages=["python"],
                matched_concepts=["formatting"],
                confidence=0.5,
            ),
        ]
        reranked = reranker.rerank(results, target_framework="fastapi", target_language="python")
        assert len(reranked) == 2
        assert reranked[0].chunk_id == "c1"
        assert reranked[0].final_score > reranked[1].final_score


class TestRetrievalEngineAndAssembler:
    """Test RetrievalEngine and ContextAssembler."""

    def test_retrieval_engine_and_assembler(self):
        # Setup mock vector store & embedding service
        provider = MockEmbeddingProvider(dimension=64)
        service = EmbeddingService(provider=provider)
        store = InMemoryVectorStore()

        # Add sample document to store
        doc = EmbeddingDocument(
            chunk_id="chunk-owasp-a01",
            document_id="OWASP-A01",
            content="Title: Broken Access Control\nCategory: security\n\n# Overview\nAuthorization checks failed in FastAPI route.",
            embedding=provider.embed_text("Broken Access Control Authorization FastAPI"),
            metadata={
                "category": "security",
                "frameworks": ["fastapi"],
                "languages": ["python"],
                "tags": ["authorization", "access-control"],
                "source_path": "/kb/a01.md",
                "title": "Broken Access Control",
            },
        )
        store.add_documents([doc])

        # Execute Retrieval Engine
        engine = RetrievalEngine(embedding_service=service, vector_store=store)
        query = RetrievalQuery(
            raw_query_string="FastAPI Broken Access Control Authorization",
            boosted_keywords=["fastapi", "authorization"],
            filters={"category": "security"},
        )
        results = engine.retrieve(query, top_k=5)
        assert len(results) >= 1
        assert results[0].document_id == "OWASP-A01"

        # Execute Context Assembler
        assembler = ContextAssembler()
        assembled = assembler.assemble_context(results)
        assert isinstance(assembled, AssembledContext)
        assert assembled.total_documents >= 1
        assert "Broken Access Control" in assembled.formatted_prompt_context
        assert len(assembled.sources) >= 1


class TestRetrievalCache:
    """Test LRU RetrievalCache."""

    def test_retrieval_cache(self):
        cache = RetrievalCache(max_size=2, ttl_seconds=60)
        query = RetrievalQuery(raw_query_string="sample query")
        results = [
            DetailedSearchResult(
                chunk_id="c1",
                document_id="d1",
                title="Test Doc",
                content="Content",
                source_path="/path.md",
                similarity_score=0.9,
            )
        ]
        cache.put("cache-key-1", results)
        assert cache.stats["size"] == 1
        cached = cache.get("cache-key-1")
        assert cached is not None
        assert cached[0].chunk_id == "c1"
