"""
Scorer helper functions for RAG ranking and normalization.
"""

import math
from typing import List

def min_max_normalize(scores: List[float]) -> List[float]:
    """
    Normalizes a list of scores to the range [0.0, 1.0] using min-max scaling.
    
    Args:
        scores: A list of float scores.
        
    Returns:
        A list of normalized scores.
    """
    if not scores:
        return []
    
    min_val = min(scores)
    max_val = max(scores)
    
    if max_val == min_val:
        return [1.0] * len(scores)
        
    return [(s - min_val) / (max_val - min_val) for s in scores]


def softmax_normalize(scores: List[float]) -> List[float]:
    """
    Normalizes a list of scores into a probability distribution using the softmax function.
    
    Args:
        scores: A list of float scores.
        
    Returns:
        A list of normalized scores summing to 1.0.
    """
    if not scores:
        return []
        
    # Shift scores by max value for numerical stability
    max_val = max(scores)
    exp_scores = [math.exp(s - max_val) for s in scores]
    sum_exp = sum(exp_scores)
    
    return [e / sum_exp for e in exp_scores]


def calculate_confidence_rating(score: float) -> str:
    """
    Calculates a confidence rating label based on a normalized score.
    
    Args:
        score: A normalized float score, typically in [0.0, 1.0].
        
    Returns:
        A string representing the confidence ("HIGH", "MEDIUM", "LOW").
    """
    if score >= 0.85:
        return "HIGH"
    elif score >= 0.60:
        return "MEDIUM"
    else:
        return "LOW"
