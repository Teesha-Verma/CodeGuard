"""Tests for ConfidenceEngine — deterministic confidence scoring validation."""
from app.reasoning.confidence_engine import ConfidenceEngine


def test_base_score_only():
    """No sources, no evidence → base score of 0.40."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=[],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []}
    )
    assert result["confidence"] == 0.40
    assert result["evidence_strength"] == "weak"


def test_single_linter_match():
    """One linter source → base (0.40) + single linter (0.20) = 0.60."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["bandit"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": [10]}
    )
    assert result["confidence"] == 0.60


def test_multiple_linter_agreement():
    """Two linter sources → base (0.40) + single (0.20) + multi (0.15) = 0.75."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["bandit", "pylint"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": [10]}
    )
    assert result["confidence"] == 0.75


def test_ast_pattern_match():
    """AST source → base (0.40) + AST (0.25) = 0.65."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["ast"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": [10]}
    )
    assert result["confidence"] == 0.65


def test_ast_with_evidence_validation():
    """AST + actual ast_nodes evidence → base (0.40) + AST (0.25) + validation (0.10) = 0.75."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["ast"],
        evidence={
            "ast_nodes": [{"node_type": "For", "line": 10, "pattern": "mutation"}],
            "linter_rules": [],
            "trigger_lines": [10]
        }
    )
    assert result["confidence"] == 0.75
    assert result["evidence_strength"] == "moderate"


def test_full_evidence_stack():
    """All signals → base (0.40) + single (0.20) + multi (0.15) + AST (0.25) = 1.10 → capped at 0.95."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["bandit", "pylint", "ast"],
        evidence={
            "ast_nodes": [{"node_type": "For", "line": 10, "pattern": "mutation"}],
            "linter_rules": [{"tool": "bandit", "rule_id": "B307", "line": 10}],
            "trigger_lines": [10]
        }
    )
    assert result["confidence"] == 0.95
    assert result["evidence_strength"] == "strong"


def test_score_never_exceeds_one():
    """Verify the cap of 0.95 is enforced regardless of input."""
    result = ConfidenceEngine.calculate(
        finding={"line": 1},
        raw_sources=["bandit", "pylint", "flake8", "ast"],
        evidence={
            "ast_nodes": [{"node_type": "X"}],
            "linter_rules": [{"tool": "bandit"}],
            "trigger_lines": [1]
        }
    )
    assert result["confidence"] <= 0.95


def test_confidence_low_signal_cap():
    """Verify low signal findings are capped at 0.60."""
    result = ConfidenceEngine.calculate(
        finding={"line": 1},
        raw_sources=["bandit"],
        evidence={
            "ast_nodes": [],
            "linter_rules": [{"tool": "bandit"}],
            "trigger_lines": [1]
        },
        signal_meta={"is_low_signal": True}
    )
    assert result["confidence"] <= 0.60
    assert any("capped at 0.60" in r or "Capped" in r for r in result["reasons"])


def test_linter_evidence_validation_bonus():
    """Linter evidence in the evidence dict grants the +0.10 validation bonus."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "issue": "test"},
        raw_sources=["flake8"],
        evidence={
            "ast_nodes": [],
            "linter_rules": [{"tool": "flake8", "rule_id": "E501", "line": 10, "message": "line too long"}],
            "trigger_lines": [10]
        }
    )
    # base (0.40) + single linter (0.20) + validation (0.10) = 0.70
    assert result["confidence"] == 0.70
    assert result["evidence_strength"] == "moderate"


def test_reasons_trace_populated():
    """Verify reasoning trace is always populated and readable."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10},
        raw_sources=["ast", "bandit"],
        evidence={"ast_nodes": [{"node_type": "X"}], "linter_rules": [], "trigger_lines": [10]}
    )
    assert len(result["reasons"]) >= 3  # base + linter + AST at minimum
    assert all(isinstance(r, str) for r in result["reasons"])


def test_confidence_b101_test_file_override():
    """B101/assert in test file should have heavily reduced confidence and reasoning suppressed."""
    result = ConfidenceEngine.calculate(
        finding={"line": 10, "rule_id": "B101", "message": "Use of assert detected"},
        raw_sources=["bandit"],
        evidence={"ast_nodes": [], "linter_rules": [{"tool": "bandit", "rule_id": "B101", "line": 10}], "trigger_lines": [10]},
        context_meta={"is_test_file": True, "is_config_file": False, "is_migration_file": False, "is_generated_file": False}
    )
    assert result["confidence"] == 0.15
    assert len(result["reasons"]) == 1
    assert "Assert statements in test files are standard practices" in result["reasons"][0]

