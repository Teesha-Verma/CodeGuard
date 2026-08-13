"""
Weighted Reranker implementation for CodeGuard V2 RAG Phase 2.
"""
from typing import List, Dict, Any, Set
from pydantic import BaseModel, Field
import hashlib

from app.analysis.RAG.search.result import DetailedSearchResult


class WeightedRerankerConfig(BaseModel):
    """Configuration for the WeightedReranker."""
    similarity_weight: float = Field(default=0.35, description="Weight for vector similarity score")
    metadata_weight: float = Field(default=0.15, description="Weight for metadata match score")
    framework_weight: float = Field(default=0.15, description="Weight for framework match score")
    language_weight: float = Field(default=0.10, description="Weight for language match score")
    security_weight: float = Field(default=0.15, description="Weight for security relevance score")
    knowledge_weight: float = Field(default=0.10, description="Weight for knowledge priority score")

    # Boost Multipliers
    framework_boost: float = Field(default=1.2, description="Boost multiplier for exact framework match")
    security_boost: float = Field(default=1.5, description="Boost multiplier for critical security relevance")
    architecture_boost: float = Field(default=1.1, description="Boost multiplier for architectural significance")
    repository_rule_boost: float = Field(default=1.3, description="Boost multiplier for repository rules")
    
    diversity_penalty: float = Field(default=0.1, description="Penalty applied to duplicate concepts")


class WeightedReranker:
    """
    Reranks candidate DetailedSearchResult items based on multi-factor scoring,
    applies boosts, and enforces deduplication and concept diversity.
    """

    def __init__(
        self,
        config: WeightedRerankerConfig = None,
        framework_boost: float | None = None,
        security_boost: float | None = None,
        architecture_boost: float | None = None,
        repository_rule_boost: float | None = None,
        **kwargs,
    ):
        """Initialize the WeightedReranker with configuration or keyword parameters."""
        if config is not None:
            self.config = config
        else:
            overrides = {}
            if framework_boost is not None:
                overrides["framework_boost"] = framework_boost
            if security_boost is not None:
                overrides["security_boost"] = security_boost
            if architecture_boost is not None:
                overrides["architecture_boost"] = architecture_boost
            if repository_rule_boost is not None:
                overrides["repository_rule_boost"] = repository_rule_boost
            for k, v in kwargs.items():
                if hasattr(WeightedRerankerConfig, k):
                    overrides[k] = v
            self.config = WeightedRerankerConfig(**overrides)

    def rerank(
        self,
        results: List[DetailedSearchResult],
        query_context: Dict[str, Any] = None,
        target_framework: str = None,
        target_language: str = None,
    ) -> List[DetailedSearchResult]:
        """
        Rerank a list of search results based on the configured weights and multipliers.
        Also applies deduplication and concept diversity enforcement.
        """
        if not results:
            return []

        if query_context is None:
            query_context = {}
        if target_framework:
            query_context["target_framework"] = target_framework
        if target_language:
            query_context["target_language"] = target_language

        scored_results = []
        seen_concepts: Set[str] = set()

        for result in results:
            new_score = self._calculate_score(result, query_context)
            concept = self._extract_primary_concept(result)
            if concept in seen_concepts:
                new_score -= self.config.diversity_penalty
            else:
                if concept:
                    seen_concepts.add(concept)

            new_score = max(0.0, new_score)

            if hasattr(result, "final_score"):
                result.final_score = new_score
            if hasattr(result, "rerank_score"):
                result.rerank_score = new_score
            if hasattr(result, "score"):
                result.score = new_score
            scored_results.append(result)

        scored_results.sort(
            key=lambda x: getattr(x, "final_score", getattr(x, "score", 0.0)),
            reverse=True,
        )

        return self._deduplicate(scored_results)

    def _calculate_score(self, result: DetailedSearchResult, query_context: Dict[str, Any]) -> float:
        base_similarity = getattr(result, "similarity_score", getattr(result, "score", 0.0))
        metadata_match = getattr(result, "metadata_score", 0.5)
        
        tf = query_context.get("target_framework", "")
        tl = query_context.get("target_language", "")

        matched_frameworks = getattr(result, "matched_frameworks", [])
        matched_languages = getattr(result, "matched_languages", [])

        framework_match = 1.0 if (tf and tf in matched_frameworks) else 0.5
        language_match = 1.0 if (tl and tl in matched_languages) else 0.5
        security_relevance = getattr(result, "confidence", 0.5)
        knowledge_priority = 0.5

        score = (
            base_similarity * self.config.similarity_weight +
            metadata_match * self.config.metadata_weight +
            framework_match * self.config.framework_weight +
            language_match * self.config.language_weight +
            security_relevance * self.config.security_weight +
            knowledge_priority * self.config.knowledge_weight
        )

        metadata = getattr(result, "raw_metadata", getattr(result, "metadata", {}))
        if metadata:
            if metadata.get("exact_framework_match") or (tf and tf in matched_frameworks):
                score *= self.config.framework_boost
            if metadata.get("category") == "security" or metadata.get("is_critical_security"):
                score *= self.config.security_boost
            if metadata.get("is_architectural_pattern"):
                score *= self.config.architecture_boost
            if metadata.get("is_repository_rule"):
                score *= self.config.repository_rule_boost

        return score

    def _extract_primary_concept(self, result: DetailedSearchResult) -> str:
        metadata = getattr(result, "raw_metadata", getattr(result, "metadata", {}))
        matched = getattr(result, "matched_concepts", [])
        if matched:
            return matched[0]
        return metadata.get("primary_concept", "")

    def _deduplicate(self, results: List[DetailedSearchResult]) -> List[DetailedSearchResult]:
        unique_results = []
        seen_hashes = set()

        for res in results:
            content = getattr(res, "content", "")
            if not content:
                unique_results.append(res)
                continue

            content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_results.append(res)

        return unique_results
