"""
Retrieval Engine for CodeGuard V2 RAG Phase 2.
"""

from typing import List, Optional

from app.analysis.RAG.embeddings.service import EmbeddingService
from app.analysis.RAG.vector_store.base import VectorStore
from app.analysis.RAG.search.result import DetailedSearchResult
from app.analysis.RAG.query_builder.builder import RetrievalQuery
from app.analysis.RAG.filters.filter_engine import MetadataFilterEngine
from app.analysis.RAG.reranker.weighted_reranker import WeightedReranker
from app.analysis.RAG.ranking.scorer import min_max_normalize


class RetrievalEngine:
    """
    Coordinates the retrieval process:
    - Embedding the query
    - Vector/Hybrid search
    - Metadata filtering
    - Score normalization
    - Reranking
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        filter_engine: Optional[MetadataFilterEngine] = None,
        reranker: Optional[WeightedReranker] = None,
    ):
        """
        Initializes the RetrievalEngine with required services.
        """
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.filter_engine = filter_engine or MetadataFilterEngine()
        self.reranker = reranker or WeightedReranker()

    def retrieve(
        self,
        query: RetrievalQuery,
        top_k: int = 10,
        hybrid_search: bool = True,
    ) -> List[DetailedSearchResult]:
        """
        Executes the full retrieval pipeline for a given query.
        """
        query_text = getattr(query, "raw_query_string", getattr(query, "text", str(query)))
        filters = getattr(query, "filters", getattr(query, "metadata_requirements", {}))

        # 1. Generate query embedding
        query_vector = self.embedding_service.embed_query(query_text)

        # 2. Similarity / Vector Search
        initial_k = top_k * 2
        search_results = self.vector_store.search(
            query_embedding=query_vector,
            top_k=initial_k,
            filters=filters,
        )

        if not search_results:
            return []

        # 3. Convert SearchResult items to DetailedSearchResult items if needed
        detailed_candidates: List[DetailedSearchResult] = []
        for sr in search_results:
            if isinstance(sr, DetailedSearchResult):
                detailed_candidates.append(sr)
            else:
                meta = getattr(sr, "metadata", {})
                detailed_candidates.append(
                    DetailedSearchResult(
                        chunk_id=getattr(sr, "chunk_id", ""),
                        document_id=getattr(sr, "document_id", ""),
                        title=meta.get("title", getattr(sr, "title", "Untitled")),
                        content=getattr(sr, "content", ""),
                        source_path=getattr(sr, "source_path", meta.get("source_path", "")),
                        similarity_score=float(getattr(sr, "score", 0.0)),
                        metadata_score=0.5,
                        matched_concepts=meta.get("tags", []),
                        matched_frameworks=meta.get("frameworks", []),
                        matched_languages=meta.get("languages", []),
                        matched_tags=meta.get("tags", []),
                        confidence=float(getattr(sr, "score", 0.5)),
                        raw_metadata=meta,
                    )
                )

        # 4. Score Normalization
        scores = [c.similarity_score for c in detailed_candidates]
        normalized_scores = min_max_normalize(scores)
        for cand, norm_score in zip(detailed_candidates, normalized_scores):
            cand.similarity_score = norm_score

        # 5. Rerank
        query_context = {"query": query_text, "filters": filters}
        reranked = self.reranker.rerank(detailed_candidates, query_context=query_context)

        # 6. Apply post filters and return top_k
        filtered = self.filter_engine.apply_post_filters(reranked, filters)
        return filtered[:top_k]
