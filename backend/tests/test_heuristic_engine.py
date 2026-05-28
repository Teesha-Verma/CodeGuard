import pytest
from app.static_analysis.heuristic_engine import HeuristicEngine
from app.reasoning.review_generator import ReviewGenerator
from app.core.config import get_settings

def test_heuristic_mutable_default():
    engine = HeuristicEngine()
    code = "def f(x=[]):\n    pass"
    findings = engine.analyze(code)
    assert len(findings) == 1
    assert findings[0]["rule_name"] == "mutable_default"
    assert findings[0]["evidence_strength"] == 1.0

def test_heuristic_broad_except():
    engine = HeuristicEngine()
    code = "try:\n    x = 1\nexcept Exception:\n    pass"
    findings = engine.analyze(code)
    assert len(findings) == 1
    assert findings[0]["rule_name"] == "broad_except"
    assert findings[0]["evidence_strength"] == 0.9

def test_heuristic_excessive_nesting():
    engine = HeuristicEngine()
    code = """
def nested(a, b, c, d):
    if a:
        if b:
            for i in range(10):
                if c:
                    print(d)
"""
    findings = engine.analyze(code)
    assert len(findings) >= 1
    assert any(f["rule_name"] == "excessive_nesting" for f in findings)

def test_reasoning_activation_bypass():
    generator = ReviewGenerator("test_review")
    # Simulate a low-signal linter finding
    aggregated = {
        "file_path": "style_file.py",
        "changed_lines": [5],
        "code_context": [],
        "ast_structural_metadata": {},
        "complexity_metrics": {},
        "scope_analysis": [],
        "control_flow": [],
        "import_analysis": {},
        "mutation_analysis": [],
        "linter_findings": [
            {
                "line": 5,
                "rule": "E501",
                "message": "line too long",
                "severity": "low",
                "tool": "flake8"
            }
        ]
    }
    issues = generator.generate(aggregated)
    assert len(issues) == 1
    issue = issues[0]
    assert issue.reasoning_source == "static_analysis"
    assert "exceeds the configured limit" in issue.root_cause
