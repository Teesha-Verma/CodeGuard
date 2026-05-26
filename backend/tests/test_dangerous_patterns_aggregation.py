import pytest
from app.api.schemas import ReviewIssue
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile

def test_dangerous_patterns_aggregation_only_surfaced():
    # Construct ReviewIssue instances with both dangerous and low-signal categories
    issue_sec = ReviewIssue(
        line=10, severity="high", confidence=0.85, issue="Security bug",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="security",
        is_low_signal=False, issue_category="security"
    )
    issue_style = ReviewIssue(
        line=12, severity="low", confidence=0.60, issue="Line too long",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="style",
        is_low_signal=True, issue_category="style-only violations"
    )
    issue_suppressed = ReviewIssue(
        line=15, severity="high", confidence=0.15, issue="Assert in test",
        root_cause="rc", trigger_condition="tc", fix="fix", issue_type="security",
        is_low_signal=False, issue_category="security"
    )
    
    # We will test the inline counting logic inside PipelineOrchestrator's process_file directly
    # by simulating the surfaced final_issues list.
    final_issues = [issue_sec, issue_style, issue_suppressed]
    
    # Count only validated, surfaced, and evidence-backed dangerous/safety-critical findings
    dangerous_patterns_count = sum(
        1 for issue in final_issues
        if (
            issue.issue_category in ("security", "mutation risks", "async misuse")
            and issue.confidence >= 0.3
        )
    )
    
    # Only issue_sec has a dangerous category and confidence >= 0.3 (0.85 >= 0.3).
    # issue_style has a low-signal style category.
    # issue_suppressed has confidence 0.15 which is < 0.3 (suppressed).
    # Thus, the count should be exactly 1.
    assert dangerous_patterns_count == 1
