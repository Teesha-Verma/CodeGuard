import logging
from typing import Any

from app.analysis.knowledge.constants import (
    DEFAULT_SIMILARITY_WEIGHT, DEFAULT_METADATA_WEIGHT, DEFAULT_CATEGORY_WEIGHT,
    DocumentCategory
)
from app.analysis.knowledge.models import RetrievalResult, RepositoryContext

logger = logging.getLogger(__name__)

class RerankerStrategy:
    """Base reranker strategy."""
    def rerank(self, results: list[RetrievalResult], context: RepositoryContext | None = None) -> list[RetrievalResult]:
        raise NotImplementedError

class WeightedReranker(RerankerStrategy):
    """
    Weighted reranking strategy.
    
    Computes final score as:
    final_score = (similarity_weight * similarity_score) +
                  (metadata_weight * metadata_score) +
                  (category_weight * category_score)
    
    Category scoring boosts results whose category aligns with the
    repository context (e.g., security findings for frameworks with known security concerns).
    """
    
    def __init__(
        self,
        similarity_weight: float = DEFAULT_SIMILARITY_WEIGHT,
        metadata_weight: float = DEFAULT_METADATA_WEIGHT,
        category_weight: float = DEFAULT_CATEGORY_WEIGHT,
        category_boosts: dict[DocumentCategory, float] | None = None,
    ):
        total_weight = similarity_weight + metadata_weight + category_weight
        if not (0.99 <= total_weight <= 1.01):
            logger.warning(f"Weights do not sum to 1.0 (sum={total_weight})")
            
        self.similarity_weight = similarity_weight
        self.metadata_weight = metadata_weight
        self.category_weight = category_weight
        self.category_boosts = category_boosts or {}
    
    def rerank(self, results: list[RetrievalResult], context: RepositoryContext | None = None) -> list[RetrievalResult]:
        try:
            for result in results:
                # 1. similarity_score already exists
                sim_score = getattr(result, 'similarity_score', 0.0)
                
                # 2. Compute metadata_score
                meta_score = self._compute_metadata_score(result)
                
                # 3. Compute category_score
                cat_score = self._compute_category_score(result, context)
                
                # 4. Combine with weights
                final_score = (
                    (self.similarity_weight * sim_score) +
                    (self.metadata_weight * meta_score) +
                    (self.category_weight * cat_score)
                )
                
                setattr(result, 'final_score', final_score)
                
            # 5. Sort by final_score descending
            results.sort(key=lambda r: getattr(r, 'final_score', getattr(r, 'similarity_score', 0.0)), reverse=True)
            return results
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            return results
    
    def _compute_metadata_score(self, result: RetrievalResult) -> float:
        """Score based on metadata richness."""
        chunk = getattr(result, 'chunk', None)
        if not chunk:
            return 0.0
            
        score = 0.0
        # Check for tags
        tags = getattr(chunk, 'tags', [])
        if tags:
            score += min(len(tags) * 0.1, 0.5)
            
        # Check for metadata dict
        metadata = getattr(chunk, 'metadata', {})
        if metadata:
            score += 0.5
            
        return min(score, 1.0)
    
    def _compute_category_score(self, result: RetrievalResult, context: RepositoryContext | None) -> float:
        """Score based on category relevance to repository context."""
        chunk = getattr(result, 'chunk', None)
        if not chunk:
            return 0.0
            
        category = getattr(chunk, 'category', None)
        if not category:
            return 0.0
            
        score = 0.5 # Base score for having a category
        
        # Apply static boost if configured
        if category in self.category_boosts:
            score += self.category_boosts[category]
            
        # Optional: apply context-based boosts
        if context:
            framework = getattr(context, 'framework', None)
            if framework and 'security' in str(category).lower():
                score += 0.2
                
        return min(score, 1.0)
