"""
Evaluator for retrieval metrics in the RAG pipeline.
"""

from typing import Any, List
import math
from pydantic import BaseModel, Field


class RetrievalMetrics(BaseModel):
    """
    Metrics for evaluating retrieval performance.
    """
    precision_at_k: float = Field(0.0, description="Precision at K")
    recall_at_k: float = Field(0.0, description="Recall at K")
    mrr: float = Field(0.0, description="Mean Reciprocal Rank")
    ndcg: float = Field(0.0, description="Normalized Discounted Cumulative Gain")
    hit_rate: float = Field(0.0, description="Hit Rate")
    coverage: float = Field(0.0, description="Coverage")
    knowledge_diversity: float = Field(0.0, description="Knowledge Diversity")


class RetrievalEvaluator:
    """
    Evaluator class to compute retrieval metrics.
    """

    def evaluate_retrieval(
        self, retrieved_docs: List[Any], expected_sources: List[str], k: int = 5
    ) -> RetrievalMetrics:
        """
        Evaluates the retrieval performance based on retrieved documents and expected sources.
        
        Args:
            retrieved_docs (List[Any]): The documents retrieved by the system.
                                        Expected to have a 'source' or 'id' attribute/key.
            expected_sources (List[str]): The ground truth sources expected to be retrieved.
            k (int): The number of top documents to consider (default is 5).
            
        Returns:
            RetrievalMetrics: The computed retrieval metrics.
        """
        top_k_docs = retrieved_docs[:k]
        
        retrieved_ids = []
        for doc in top_k_docs:
            doc_id = ""
            if isinstance(doc, dict):
                doc_id = doc.get("source_path") or doc.get("source") or doc.get("document_id") or doc.get("id") or str(doc)
            else:
                doc_id = getattr(doc, "source_path", getattr(doc, "source", getattr(doc, "document_id", getattr(doc, "id", str(doc)))))
            retrieved_ids.append(str(doc_id))
                
        relevant_retrieved = [doc_id for doc_id in retrieved_ids if doc_id in expected_sources]
        precision = len(relevant_retrieved) / k if k > 0 else 0.0
        
        recall = len(relevant_retrieved) / len(expected_sources) if expected_sources else 0.0
        
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_sources:
                mrr = 1.0 / (i + 1)
                break
                
        dcg = 0.0
        for i, doc_id in enumerate(retrieved_ids):
            if doc_id in expected_sources:
                dcg += 1.0 / math.log2(i + 2)
                
        idcg = 0.0
        for i in range(min(len(expected_sources), k)):
            idcg += 1.0 / math.log2(i + 2)
            
        ndcg = dcg / idcg if idcg > 0 else 0.0
        
        hit_rate = 1.0 if relevant_retrieved else 0.0
        
        coverage = len(set(relevant_retrieved)) / len(set(expected_sources)) if expected_sources else 0.0
        knowledge_diversity = len(set(retrieved_ids)) / k if k > 0 else 0.0
        
        return RetrievalMetrics(
            precision_at_k=precision,
            recall_at_k=recall,
            mrr=mrr,
            ndcg=ndcg,
            hit_rate=hit_rate,
            coverage=coverage,
            knowledge_diversity=knowledge_diversity
        )
