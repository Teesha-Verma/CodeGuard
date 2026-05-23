"""Tests for Phase 3 — Confidence Engine context-aware calibrations.

These tests validate the NEW calibration features (high-priority bonus,
low-signal penalty, test/config file discounts, high-precision AST bonus,
and score clamping) WITHOUT breaking the existing V1 formula tested in
test_confidence.py.
"""
from app.reasoning.confidence_engine import ConfidenceEngine


def test_high_priority_bonus():
    """High-priority signal should add +0.15 to the score."""
    base_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=[],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    boosted_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=[],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        signal_meta={"signal_priority": "high", "is_low_signal": False},
    )
    assert boosted_result["confidence"] == round(base_result["confidence"] + 0.15, 2)
    assert any("+0.15" in r and "High-priority" in r for r in boosted_result["reasons"])


def test_low_signal_penalty():
    """Low-signal findings should subtract -0.15 from the score."""
    base_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["flake8"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    penalized_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["flake8"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        signal_meta={"signal_priority": "low", "is_low_signal": True},
    )
    assert penalized_result["confidence"] == round(base_result["confidence"] - 0.15, 2)
    assert any("Low-signal" in r for r in penalized_result["reasons"])


def test_test_file_discount_non_security():
    """Test files should get -0.15 discount for non-security findings."""
    base_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["ast"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    discounted_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["ast"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        context_meta={"is_test_file": True},
        signal_meta={"issue_category": "runtime logic risks"},
    )
    assert discounted_result["confidence"] == round(base_result["confidence"] - 0.15, 2)
    assert any("Test-file" in r for r in discounted_result["reasons"])


def test_test_file_discount_not_applied_to_security():
    """Security findings inside test files should NOT get the discount."""
    base_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["bandit"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    same_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["bandit"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        context_meta={"is_test_file": True},
        signal_meta={"issue_category": "security"},
    )
    assert same_result["confidence"] == base_result["confidence"]
    assert not any("Test-file" in r for r in same_result["reasons"])


def test_config_file_discount():
    """Config files should get -0.10 discount."""
    base_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["flake8"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    discounted_result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["flake8"],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        context_meta={"is_config_file": True},
    )
    assert discounted_result["confidence"] == round(base_result["confidence"] - 0.10, 2)
    assert any("Config-file" in r for r in discounted_result["reasons"])


def test_high_precision_ast_bonus():
    """High-precision AST rules (eval, exec, subprocess, pickle) get +0.15."""
    result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["ast"],
        evidence={
            "ast_nodes": [{"rule_name": "eval_detection", "line": 5}],
            "linter_rules": [],
            "trigger_lines": [5],
        },
    )
    # base(0.40) + ast(0.25) + evidence_validation(0.10) + high_precision(0.15) = 0.90
    assert result["confidence"] == 0.90
    assert any("High-precision" in r for r in result["reasons"])


def test_score_floor_clamp():
    """Score should never drop below 0.10 even with extreme penalties."""
    result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=[],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
        context_meta={"is_test_file": True, "is_config_file": True},
        signal_meta={"signal_priority": "low", "is_low_signal": True, "issue_category": "style-only violations"},
    )
    # base(0.40) - low_signal(0.15) - test_file(0.15) - config_file(0.10) = 0.00 → clamped to 0.10
    assert result["confidence"] >= 0.10
    assert result["confidence"] == 0.10


def test_combined_calibrations():
    """Multiple calibrations stack correctly."""
    result = ConfidenceEngine.calculate(
        finding={"line": 5},
        raw_sources=["bandit", "ast"],
        evidence={
            "ast_nodes": [{"rule_name": "unsafe_subprocess", "line": 5}],
            "linter_rules": [{"tool": "bandit", "rule_id": "B602", "line": 5}],
            "trigger_lines": [5],
        },
        signal_meta={"signal_priority": "high", "is_low_signal": False, "issue_category": "security"},
    )
    # base(0.40) + linter(0.20) + ast(0.25) + evidence(0.10) + high_priority(0.15)
    # + high_precision(0.15) = 1.25 → capped to 0.95
    assert result["confidence"] == 0.95
    assert result["evidence_strength"] == "strong"


def test_reasons_trace_always_has_base():
    """Every result should always start with the base confidence reason."""
    result = ConfidenceEngine.calculate(
        finding={"line": 1},
        raw_sources=[],
        evidence={"ast_nodes": [], "linter_rules": [], "trigger_lines": []},
    )
    assert any("Base confidence" in r for r in result["reasons"])
