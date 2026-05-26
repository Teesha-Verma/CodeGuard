import pytest
from app.evaluation.metrics import MetricsCalculator
from app.api.schemas import ReviewIssue, FileReport, ReviewReport

def test_summary_stats_separation():
    # 1. Prepare raw issues representing different categories
    raw_issues = [
        # Safety-critical / meaningful issues (not low-signal, high confidence)
        {"severity": "high", "confidence": 0.85, "sources": ["ast"], "is_low_signal": False},
        {"severity": "critical", "confidence": 0.90, "sources": ["ast", "linter"], "is_low_signal": False},
        
        # Style-only warnings (low-signal, moderate confidence)
        {"severity": "low", "confidence": 0.60, "sources": ["flake8"], "is_low_signal": True},
        {"severity": "low", "confidence": 0.50, "sources": ["pylint"], "is_low_signal": True},
        
        # Suppressed issues (very low confidence < 0.3)
        {"severity": "low", "confidence": 0.15, "sources": ["bandit"], "is_low_signal": True},
        {"severity": "medium", "confidence": 0.20, "sources": ["ast"], "is_low_signal": False}
    ]
    
    stats = MetricsCalculator.compute_summary_stats(raw_issues)
    
    # Verify separation counts
    assert stats["meaningful_issues"] == 2
    assert stats["style_findings"] == 2
    assert stats["suppressed_findings"] == 2
    
    # Ensure total_issues is NOT inflated (only counts meaningful safety-critical issues)
    assert stats["total_issues"] == 2
    assert stats["evaluation_available"] is True


def test_schema_auto_categorization():
    # Construct ReviewIssue instances
    issue_meaningful = ReviewIssue(
        line=10, severity="high", confidence=0.85, issue="Logic bug",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="bug",
        is_low_signal=False
    )
    issue_style = ReviewIssue(
        line=12, severity="low", confidence=0.60, issue="Line too long",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="style",
        is_low_signal=True
    )
    issue_suppressed = ReviewIssue(
        line=15, severity="low", confidence=0.15, issue="Assert in test",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="style",
        is_low_signal=True
    )
    
    # Test FileReport auto-categorization
    file_report = FileReport(
        file_path="app/main.py",
        issues=[issue_meaningful, issue_style, issue_suppressed]
    )
    
    assert len(file_report.meaningful_issues) == 1
    assert file_report.meaningful_issues[0].issue == "Logic bug"
    
    assert len(file_report.style_findings) == 1
    assert file_report.style_findings[0].issue == "Line too long"
    
    assert len(file_report.suppressed_findings) == 1
    assert file_report.suppressed_findings[0].issue == "Assert in test"
    
    # Test ReviewReport auto-aggregation
    review_report = ReviewReport(
        review_id="rev-123",
        file_reports=[file_report],
        trace_id="rev-123"
    )
    
    assert len(review_report.meaningful_issues) == 1
    assert len(review_report.style_findings) == 1
    assert len(review_report.suppressed_findings) == 1
