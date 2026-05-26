import pytest
from app.evaluation.metrics import MetricsCalculator

def test_source_attribution_separated():
    # 1. Test direct mapping with explicitly populated lists
    issues = [
        {
            "severity": "high",
            "confidence": 0.85,
            "sources": ["flake8", "static_analysis"],
            "detection_sources": ["flake8"],
            "reasoning_source": "static_analysis"
        },
        {
            "severity": "critical",
            "confidence": 0.90,
            "sources": ["bandit", "llm"],
            "detection_sources": ["bandit"],
            "reasoning_source": "llm"
        }
    ]
    
    stats = MetricsCalculator.compute_summary_stats(issues)
    
    assert "detection_sources" in stats
    assert "reasoning_sources" in stats
    
    assert stats["detection_sources"]["flake8"] == 1
    assert stats["detection_sources"]["bandit"] == 1
    assert stats["reasoning_sources"]["static_analysis"] == 1
    assert stats["reasoning_sources"]["llm"] == 1


def test_source_attribution_legacy_fallback():
    # 2. Test legacy fallback mapping when only the standard 'sources' and 'reasoning_source' lists are available
    issues_legacy = [
        {
            "severity": "high",
            "confidence": 0.85,
            "sources": ["flake8", "static_analysis"],
            "reasoning_source": "static_analysis"
        },
        {
            "severity": "critical",
            "confidence": 0.90,
            "sources": ["bandit", "llm"],
            "reasoning_source": "llm"
        }
    ]
    
    stats = MetricsCalculator.compute_summary_stats(issues_legacy)
    
    assert stats["detection_sources"]["flake8"] == 1
    assert stats["detection_sources"]["bandit"] == 1
    assert stats["reasoning_sources"]["static_analysis"] == 1
    assert stats["reasoning_sources"]["llm"] == 1
