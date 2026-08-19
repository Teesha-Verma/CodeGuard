"""
CodeGuard V2 — Knowledge Retrieval & Grounding Service.

Connects the RAG knowledge repository (419 security/python/orm rules),
semantic query construction, Gemini Embedding 2 retrieval, and prompt context assembly.
"""
from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from app.analysis.RAG.config.settings import RAGConfig
from app.analysis.RAG.embeddings.base import EmbeddingProvider
from app.analysis.RAG.embeddings.gemini_provider import GeminiEmbeddingProvider
from app.analysis.RAG.embeddings.mock_provider import MockEmbeddingProvider
from app.analysis.RAG.embeddings.service import EmbeddingService
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
from app.analysis.RAG.query_builder.builder import QueryBuilder, RetrievalQuery
from app.analysis.RAG.retrieval.engine import RetrievalEngine
from app.analysis.RAG.context.assembler import ContextAssembler, AssembledContext
from app.analysis.RAG.context.base import RetrievalContextSignal
from app.analysis.RAG.ingestion.pipeline import IndexingPipeline
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class KnowledgeRetrievalService:
    """
    Orchestrates RAG knowledge retrieval for review analysis.
    Maintains an in-memory vector index of the 419 knowledge documents.
    """

    _instance: Optional[KnowledgeRetrievalService] = None

    def __init__(
        self,
        config: Optional[RAGConfig] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
        vector_store: Optional[InMemoryVectorStore] = None,
        auto_index: bool = True,
    ):
        self.settings = get_settings()
        self.config = config or RAGConfig.from_env()

        # Set resolved knowledge path
        resolved_kb_dir = self.settings.get_resolved_knowledge_path()
        if os.path.isdir(resolved_kb_dir):
            self.config.knowledge_dir = resolved_kb_dir

        # Configure embedding provider
        if embedding_provider is not None:
            self.embedding_provider = embedding_provider
        elif (
            self.settings.LLM_PROVIDER in ("mock", "mock_gemini")
            or not self.settings.GEMINI_API_KEY
            or self.settings.GEMINI_API_KEY in ("mock_key", "your_gemini_api_key_here")
        ):
            self.embedding_provider = MockEmbeddingProvider(dimension=self.config.embedding.dimension or 768)
        else:
            self.embedding_provider = GeminiEmbeddingProvider(
                api_key=self.settings.GEMINI_API_KEY,
                model=self.config.embedding.model or "gemini-embedding-2",
                dimension=self.config.embedding.dimension or 768,
            )

        self.vector_store = vector_store or InMemoryVectorStore(dimension=self.embedding_provider.dimension)
        self.embedding_service = EmbeddingService(provider=self.embedding_provider)
        self.retrieval_engine = RetrievalEngine(
            embedding_service=self.embedding_service,
            vector_store=self.vector_store,
        )
        self.query_builder = QueryBuilder()
        self.assembler = ContextAssembler()
        self._is_indexed = False

        if auto_index and self.vector_store.count() == 0:
            self.index_knowledge_base()

    def index_knowledge_base(self, force_reindex: bool = False) -> int:
        """Indexes all markdown knowledge documents into the vector store."""
        try:
            pipeline = IndexingPipeline(
                config=self.config,
                embedding_provider=self.embedding_provider,
                vector_store=self.vector_store,
            )
            stats = pipeline.run(force_reindex=force_reindex)
            self._is_indexed = True
            logger.info(f"RAG Knowledge Indexing complete: {stats.vectors_stored} vectors stored from {stats.files_parsed} files.")
            return stats.vectors_stored
        except Exception as e:
            logger.warning(f"Could not auto-index knowledge base: {e}")
            return 0

    def retrieve_for_finding(
        self,
        finding: Dict[str, Any],
        repo_context: Optional[Dict[str, Any]] = None,
        top_k: int = 3,
    ) -> AssembledContext:
        """
        Constructs a targeted semantic retrieval query from a finding and retrieves matching knowledge.
        """
        signals = []

        # Extract tokens from finding
        issue_text = finding.get("issue", "")
        severity = finding.get("severity", "medium")
        sources = finding.get("sources", [])
        evidence = finding.get("evidence", {})

        keywords = []
        vuln_types = []

        # Check for OWASP / CWE or security terms
        issue_lower = issue_text.lower()
        if "sql" in issue_lower:
            vuln_types.extend(["CWE-89", "sql_injection", "owasp_a03"])
            keywords.extend(["sql", "injection", "parameterization", "orm"])
        elif "command" in issue_lower or "subprocess" in issue_lower or "exec" in issue_lower or "eval" in issue_lower:
            vuln_types.extend(["CWE-78", "CWE-94", "command_injection"])
            keywords.extend(["command", "injection", "subprocess", "eval", "exec"])
        elif "deserialize" in issue_lower or "pickle" in issue_lower:
            vuln_types.extend(["CWE-502", "unsafe_deserialization"])
            keywords.extend(["pickle", "deserialization", "untrusted"])
        elif "path" in issue_lower or "file" in issue_lower or "traversal" in issue_lower:
            vuln_types.extend(["CWE-22", "path_traversal"])
            keywords.extend(["path", "traversal", "file", "directory"])
        elif "mutation" in issue_lower:
            vuln_types.append("mutation_risks")
            keywords.extend(["mutation", "iteration", "list", "dictionary"])
        elif "async" in issue_lower:
            vuln_types.append("async_misuse")
            keywords.extend(["async", "await", "coroutine", "event_loop"])
        elif "shadow" in issue_lower:
            vuln_types.append("variable_shadowing")
            keywords.extend(["shadowing", "scope", "variable"])
        else:
            keywords.append(issue_text[:50])

        signal = RetrievalContextSignal(
            signal_type="finding_signal",
            vulnerability_types=vuln_types,
            query_tokens=keywords,
            languages=["python"],
            frameworks=[repo_context.get("framework", "")] if repo_context and repo_context.get("framework") else [],
            databases=[repo_context.get("database", "")] if repo_context and repo_context.get("database") else [],
            tags=[severity],
        )
        signals.append(signal)

        retrieval_query = self.query_builder.build_query(signals)
        results = self.retrieval_engine.retrieve(retrieval_query, top_k=top_k)
        return self.assembler.assemble_context(results)

    @classmethod
    def get_instance(cls) -> KnowledgeRetrievalService:
        """Get or initialize singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
