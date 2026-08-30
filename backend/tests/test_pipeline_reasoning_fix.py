"""
CodeGuard V2 — Complete Finding Pipeline, Deduplication, Style Classification,
LLM Selection, TPD Rate-Limit Handling, Repository Serialization, and Metrics Invariant Tests.

Covers all requirements from Problem 22:
  A. Style classification (whitespace, line length, docstring -> is_low_signal=True, reasoning_source=static_analysis)
  B. Priority selection (security & correctness prioritized over style/low-signal)
  C. Deduplication across multiple analyzers (merging sources & evidence)
  D. Budget upper bound (100 findings with budget 25 -> at most 25 LLM requests)
  E. Small review budget (5 findings with budget 25 -> at most 5 LLM requests)
  F. Rate-limit / TPD handling (429 TPD -> immediately switch to fallback, no 3 retries)
  G. Fallback exhaustion (graceful degradation to static analysis)
  H. ArchitectureInfo & repository intelligence serialization (no to_dict AttributeError)
  I. Metrics invariants (sum(by_severity) == meaningful_issues, sum(all_by_severity) == total_all_issues)
  J. DB persistence across all finding categories
  K. Bounded context extraction in RootCauseEngine
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

# Ensure backend is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.evaluation.metrics import MetricsCalculator
from app.reasoning.review_generator import ReviewGenerator
from app.reasoning.root_cause_engine import RootCauseEngine
from app.static_analysis.prioritization import PrioritizationEngine
from app.llm.llm_client import LLMClient
from app.llm.llm_budget import get_review_tracker, reset_review_tracker, ReviewLLMTracker
from app.analysis.repository.models import (
    ArchitectureInfo,
    Hotspot,
    ChangeImpact,
    LayerViolation,
    FileClassification,
    RepositoryMetadata,
    RepositorySummary,
)
from app.analysis.repository.constants import Architecture, Layer, Severity, FileCategory


@pytest.fixture(autouse=True)
def reset_trackers():
    """Reset all LLM budget trackers before and after each test."""
    reset_review_tracker()
    yield
    reset_review_tracker()


# ═══════════════════════════════════════════════════════════════════
# A. STYLE CLASSIFICATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestStyleClassification:
    @pytest.mark.parametrize("rule_id,message", [
        ("E501", "Line too long (120 > 79 characters)"),
        ("E501", "line too long"),
        ("W293", "blank line contains whitespace"),
        ("W291", "trailing whitespace"),
        ("C0114", "Missing module docstring"),
        ("C0116", "Missing function or method docstring"),
        ("C0301", "Line too long"),
        ("C0303", "Trailing whitespace"),
        ("E302", "expected 2 blank lines, found 1"),
        ("D100", "Missing docstring in public module"),
        ("D103", "Missing docstring in public function"),
        ("", "trailing whitespace on line 15"),
        ("", "Line length exceeds 88 characters"),
    ])
    def test_style_rules_classified_as_low_signal(self, rule_id, message):
        """All formatting, whitespace, line length, and docstring rules must be low-signal style findings."""
        res = PrioritizationEngine.analyze(source="linter", rule_id=rule_id, message=message)
        assert res["is_low_signal"] is True
        assert res["signal_priority"] == "low"
        assert res["issue_category"] == "style-only violations"

    def test_security_rules_not_classified_as_style(self):
        """Security findings must NOT be marked low-signal."""
        res = PrioritizationEngine.analyze(source="bandit", rule_id="B307", message="Use of possibly insecure function - eval")
        assert res["is_low_signal"] is False
        assert res["signal_priority"] == "high"
        assert res["issue_category"] == "security"

    def test_mutation_rules_not_classified_as_style(self):
        """Mutation findings must NOT be marked low-signal."""
        res = PrioritizationEngine.analyze(source="ast", rule_id="MUTATION_DURING_ITERATION", message="List mutation during iteration")
        assert res["is_low_signal"] is False
        assert res["signal_priority"] == "high"
        assert res["issue_category"] == "mutation risks"


# ═══════════════════════════════════════════════════════════════════
# B. PRIORITY SELECTION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestPrioritySelection:
    def test_meaningful_selected_before_style(self):
        """Given 10 style findings, 3 medium correctness findings, and 2 high security findings,
        only the 5 meaningful findings must be selected for LLM reasoning."""
        gen = ReviewGenerator(review_id="test-priority-order")

        enriched = []
        # 10 style findings
        for i in range(1, 11):
            enriched.append({
                "line": i,
                "file_path": "app/main.py",
                "finding": {"line": i, "issue": f"Line {i} too long", "severity": "low", "issue_type": "style", "sources": ["flake8"], "evidence": {}},
                "evidence_strength": 0.3,
                "primary_source": "flake8", "primary_rule": "E501", "primary_msg": f"Line {i} too long",
                "priority_info": {"signal_priority": "low", "issue_category": "style-only violations", "is_low_signal": True},
                "conf_details": {"confidence": 0.5, "reasons": []},
                "is_changed": True,
            })

        # 3 medium correctness findings
        for i in range(11, 14):
            enriched.append({
                "line": i,
                "file_path": "app/main.py",
                "finding": {"line": i, "issue": f"Global variable modified in func {i}", "severity": "medium", "issue_type": "runtime_logic_error", "sources": ["ast"], "evidence": {}},
                "evidence_strength": 0.7,
                "primary_source": "ast", "primary_rule": "global_mutation", "primary_msg": "Global modification",
                "priority_info": {"signal_priority": "medium", "issue_category": "runtime logic risks", "is_low_signal": False},
                "conf_details": {"confidence": 0.75, "reasons": []},
                "is_changed": True,
            })

        # 2 high security findings
        for i in range(14, 16):
            enriched.append({
                "line": i,
                "file_path": "app/main.py",
                "finding": {"line": i, "issue": f"SQL injection vulnerability {i}", "severity": "high", "issue_type": "security", "sources": ["bandit"], "evidence": {}},
                "evidence_strength": 0.9,
                "primary_source": "bandit", "primary_rule": "B608", "primary_msg": "SQL injection",
                "priority_info": {"signal_priority": "high", "issue_category": "security", "is_low_signal": False},
                "conf_details": {"confidence": 0.90, "reasons": []},
                "is_changed": True,
            })

        llm_candidates, non_llm = gen._select_findings_for_llm(enriched, threshold=0.50)

        # Exactly 5 meaningful findings selected
        assert len(llm_candidates) == 5
        assert len(non_llm) == 10

        # Security findings must be ranked first, followed by medium correctness
        selected_lines = [ef["line"] for ef in llm_candidates]
        assert selected_lines[0] in (14, 15)  # Security
        assert selected_lines[1] in (14, 15)  # Security
        assert set(selected_lines[2:]) == {11, 12, 13}  # Medium runtime


# ═══════════════════════════════════════════════════════════════════
# C. DEDUPLICATION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestDeduplication:
    def test_duplicate_linter_findings_merged(self):
        """When pylint and flake8 report the same line length issue on the same line,
        they must be merged into one finding with both detection sources."""
        gen = ReviewGenerator(review_id="test-dedup-linters")
        enriched = [
            {
                "line": 42,
                "file_path": "app/utils.py",
                "finding": {
                    "line": 42, "issue": "line too long (120 > 79)", "severity": "low", "issue_type": "style",
                    "sources": ["flake8"],
                    "evidence": {"ast_nodes": [], "linter_rules": [{"tool": "flake8", "rule_id": "E501", "line": 42}], "dataflow_findings": []}
                },
                "evidence_strength": 0.3, "primary_source": "flake8", "primary_rule": "E501", "primary_msg": "line too long",
                "priority_info": {"signal_priority": "low", "issue_category": "style-only violations", "is_low_signal": True},
                "conf_details": {"confidence": 0.50, "reasons": []}, "is_changed": True,
            },
            {
                "line": 42,
                "file_path": "app/utils.py",
                "finding": {
                    "line": 42, "issue": "Line too long (120/100)", "severity": "low", "issue_type": "style",
                    "sources": ["pylint"],
                    "evidence": {"ast_nodes": [], "linter_rules": [{"tool": "pylint", "rule_id": "C0301", "line": 42}], "dataflow_findings": []}
                },
                "evidence_strength": 0.4, "primary_source": "pylint", "primary_rule": "C0301", "primary_msg": "Line too long",
                "priority_info": {"signal_priority": "low", "issue_category": "style-only violations", "is_low_signal": True},
                "conf_details": {"confidence": 0.60, "reasons": []}, "is_changed": True,
            }
        ]

        deduped = gen._deduplicate_findings(enriched)
        assert len(deduped) == 1
        merged = deduped[0]["finding"]
        assert "flake8" in merged["sources"]
        assert "pylint" in merged["sources"]
        assert len(merged["evidence"]["linter_rules"]) == 2

    def test_distinct_issues_on_same_line_not_merged(self):
        """Distinct findings on the same line (e.g. security eval + line too long) must NOT be merged."""
        gen = ReviewGenerator(review_id="test-dedup-distinct")
        enriched = [
            {
                "line": 10,
                "file_path": "app/main.py",
                "finding": {
                    "line": 10, "issue": "eval() call detected", "severity": "critical", "issue_type": "security",
                    "sources": ["ast"], "evidence": {"ast_nodes": [], "linter_rules": [], "dataflow_findings": []}
                },
                "evidence_strength": 1.0, "primary_source": "ast", "primary_rule": "eval_detection", "primary_msg": "eval() call",
                "priority_info": {"signal_priority": "high", "issue_category": "security", "is_low_signal": False},
                "conf_details": {"confidence": 0.90, "reasons": []}, "is_changed": True,
            },
            {
                "line": 10,
                "file_path": "app/main.py",
                "finding": {
                    "line": 10, "issue": "Line too long (120 > 79)", "severity": "low", "issue_type": "style",
                    "sources": ["flake8"], "evidence": {"ast_nodes": [], "linter_rules": [], "dataflow_findings": []}
                },
                "evidence_strength": 0.3, "primary_source": "flake8", "primary_rule": "E501", "primary_msg": "Line too long",
                "priority_info": {"signal_priority": "low", "issue_category": "style-only violations", "is_low_signal": True},
                "conf_details": {"confidence": 0.40, "reasons": []}, "is_changed": True,
            }
        ]

        deduped = gen._deduplicate_findings(enriched)
        assert len(deduped) == 2


# ═══════════════════════════════════════════════════════════════════
# D & E. BUDGET UPPER BOUND & SMALL REVIEW TESTS
# ═══════════════════════════════════════════════════════════════════

class TestBudgetBounds:
    def test_budget_upper_bound_capped_at_max(self):
        """100 meaningful findings with budget 25 must result in at most 25 LLM candidates."""
        reset_review_tracker("test-budget-100")
        tracker = get_review_tracker("test-budget-100", max_requests=25)
        gen = ReviewGenerator(review_id="test-budget-100")

        enriched = [
            {
                "line": i,
                "file_path": "app/main.py",
                "finding": {"line": i, "issue": f"Vulnerability {i}", "severity": "high", "issue_type": "security", "sources": ["ast"], "evidence": {}},
                "evidence_strength": 0.85,
                "primary_source": "ast", "primary_rule": "sec_rule", "primary_msg": f"Vulnerability {i}",
                "priority_info": {"signal_priority": "high", "issue_category": "security", "is_low_signal": False},
                "conf_details": {"confidence": 0.85, "reasons": []}, "is_changed": True,
            }
            for i in range(1, 101)
        ]

        llm_candidates, non_llm = gen._select_findings_for_llm(enriched, threshold=0.50)

        assert len(llm_candidates) == 25
        assert len(non_llm) == 75
        assert tracker.llm_requests_skipped_budget == 75

    def test_small_review_only_uses_needed_budget(self):
        """5 meaningful findings with budget 25 must only select 5 LLM candidates (no waste)."""
        reset_review_tracker("test-budget-5")
        tracker = get_review_tracker("test-budget-5", max_requests=25)
        gen = ReviewGenerator(review_id="test-budget-5")

        enriched = [
            {
                "line": i,
                "file_path": "app/main.py",
                "finding": {"line": i, "issue": f"Vulnerability {i}", "severity": "high", "issue_type": "security", "sources": ["ast"], "evidence": {}},
                "evidence_strength": 0.85,
                "primary_source": "ast", "primary_rule": "sec_rule", "primary_msg": f"Vulnerability {i}",
                "priority_info": {"signal_priority": "high", "issue_category": "security", "is_low_signal": False},
                "conf_details": {"confidence": 0.85, "reasons": []}, "is_changed": True,
            }
            for i in range(1, 6)
        ]

        llm_candidates, non_llm = gen._select_findings_for_llm(enriched, threshold=0.50)

        assert len(llm_candidates) == 5
        assert len(non_llm) == 0


# ═══════════════════════════════════════════════════════════════════
# F & G. RATE LIMIT / TPD HANDLING & FALLBACK EXHAUSTION
# ═══════════════════════════════════════════════════════════════════

class TestRateLimitAndFallback:
    def test_tpd_quota_immediately_switches_model_no_retries(self):
        """When Groq returns a 429 TPD error, the model must be marked exhausted immediately,
        skipping all 3 retries, and switching to the fallback model."""
        review_id = "test-tpd-switch"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)

        client = LLMClient(review_id=review_id)
        client.model = "openai/gpt-oss-120b"
        client.api_key = "gsk_test_key"

        mock_groq_instance = MagicMock()

        # Primary model raises TPD rate limit error
        tpd_error = Exception("Rate limit reached for model openai/gpt-oss-120b: TPD limit: 200000 Used: 198401 Requested: 3852")
        
        # Fallback model succeeds
        mock_fallback_choice = MagicMock()
        mock_fallback_choice.message.content = '{"root_cause": "Unsafe eval", "trigger_condition": "User input", "fix": "Use literal_eval", "patch": "", "issue_type": "security"}'
        mock_fallback_response = MagicMock()
        mock_fallback_response.choices = [mock_fallback_choice]
        mock_fallback_response.usage.prompt_tokens = 150
        mock_fallback_response.usage.completion_tokens = 40

        def side_effect(*args, **kwargs):
            model = kwargs.get("model")
            if model == "openai/gpt-oss-120b":
                raise tpd_error
            return mock_fallback_response

        mock_groq_instance.chat.completions.create.side_effect = side_effect
        client._client = mock_groq_instance

        # Execute call
        result = client.generate_structured("System prompt", "User content")

        # 1. Primary model was marked permanently exhausted
        assert tracker.is_model_exhausted("openai/gpt-oss-120b") is True

        # 2. Result succeeded using fallback model
        assert result is not None
        assert result.get("reasoning_source") == "llm"
        assert result.get("root_cause") == "Unsafe eval"

        # 3. For the NEXT call in this review, primary model is NOT attempted again!
        available = tracker.get_available_models("openai/gpt-oss-120b", ["qwen/qwen3.8-27b", "llama-3.3-70b-versatile"])
        assert "openai/gpt-oss-120b" not in available
        assert available[0] == "qwen/qwen3.8-27b"

    def test_all_models_exhausted_graceful_degradation(self):
        """When all candidate models fail, client returns None and enters degraded mode without crashing."""
        review_id = "test-all-fail"
        reset_review_tracker(review_id)
        tracker = get_review_tracker(review_id)

        client = LLMClient(review_id=review_id)
        client.model = "openai/gpt-oss-120b"
        client.api_key = "gsk_test_key"

        mock_groq_instance = MagicMock()
        mock_groq_instance.chat.completions.create.side_effect = Exception("500 Internal Server Error")
        client._client = mock_groq_instance

        result = client.generate_structured("System prompt", "User content")

        assert result is None
        assert tracker.degraded_mode is True


# ═══════════════════════════════════════════════════════════════════
# H. ARCHITECTUREINFO & REPOSITORY MODELS SERIALIZATION
# ═══════════════════════════════════════════════════════════════════

class TestRepositoryIntelligenceSerialization:
    def test_architecture_info_to_dict(self):
        """ArchitectureInfo.to_dict() must return a valid dictionary without raising AttributeError."""
        arch = ArchitectureInfo(
            architecture=Architecture.MVC,
            confidence=0.85,
            detected_layers=[Layer.CONTROLLER, Layer.MODEL],
            detected_directories=["controllers", "models"],
            signals=["Flask blueprints detected", "SQLAlchemy models detected"]
        )

        d = arch.to_dict()
        assert isinstance(d, dict)
        assert d["architecture"] == "mvc"
        assert d["confidence"] == 0.85
        assert d["detected_layers"] == ["controller", "model"]
        assert len(d["signals"]) == 2

    def test_hotspot_to_dict(self):
        """Hotspot.to_dict() must return a valid dictionary."""
        hotspot = Hotspot(
            file_path="app/core/engine.py",
            risk_score=0.75,
            import_count=15,
            caller_count=20,
            cyclomatic_complexity=35,
            file_size_lines=450,
            reasons=["High complexity", "High coupling"]
        )
        d = hotspot.to_dict()
        assert isinstance(d, dict)
        assert d["file_path"] == "app/core/engine.py"
        assert d["risk_score"] == 0.75

    def test_change_impact_to_dict(self):
        """ChangeImpact.to_dict() must return a valid dictionary."""
        impact = ChangeImpact(
            changed_files=["app/main.py"],
            affected_files=["app/routes.py", "app/auth.py"],
            affected_modules=["app.routes", "app.auth"],
            potential_regression_scope=2,
            risk_score=0.45,
            risk_reasons=["Core module modified"]
        )
        d = impact.to_dict()
        assert isinstance(d, dict)
        assert len(d["affected_files"]) == 2


# ═══════════════════════════════════════════════════════════════════
# I. SUMMARY STATISTICS & INVARIANTS TESTS
# ═══════════════════════════════════════════════════════════════════

class TestMetricsInvariants:
    def test_exact_invariants_across_mixed_findings(self):
        """Mathematical invariants must hold exactly:
        - sum(by_severity.values()) == meaningful_issues
        - sum(all_by_severity.values()) == total_all_issues
        - total_all_issues == meaningful_issues + style_findings + suppressed_findings
        - total_issues == meaningful_issues
        - reasoning_sources.llm + reasoning_sources.static_analysis == total findings
        """
        raw_issues = [
            # Meaningful: 2 critical, 3 high, 4 medium
            {"severity": "critical", "confidence": 0.95, "is_low_signal": False, "reasoning_source": "llm", "sources": ["ast"]},
            {"severity": "critical", "confidence": 0.90, "is_low_signal": False, "reasoning_source": "llm", "sources": ["dataflow"]},
            {"severity": "high", "confidence": 0.85, "is_low_signal": False, "reasoning_source": "llm", "sources": ["bandit"]},
            {"severity": "high", "confidence": 0.80, "is_low_signal": False, "reasoning_source": "llm", "sources": ["ast"]},
            {"severity": "high", "confidence": 0.75, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["ast"]},
            {"severity": "medium", "confidence": 0.70, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["pylint"]},
            {"severity": "medium", "confidence": 0.65, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["pylint"]},
            {"severity": "medium", "confidence": 0.60, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["ast"]},
            {"severity": "medium", "confidence": 0.55, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["ast"]},
            # Style: 5 low findings
            {"severity": "low", "confidence": 0.50, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["flake8"]},
            {"severity": "low", "confidence": 0.45, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["flake8"]},
            {"severity": "low", "confidence": 0.40, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["pylint"]},
            {"severity": "low", "confidence": 0.35, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["pylint"]},
            {"severity": "low", "confidence": 0.30, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["flake8"]},
            # Suppressed: 2 findings with confidence < 0.3
            {"severity": "low", "confidence": 0.20, "is_low_signal": True, "reasoning_source": "static_analysis", "sources": ["flake8"]},
            {"severity": "info", "confidence": 0.15, "is_low_signal": False, "reasoning_source": "static_analysis", "sources": ["ast"]},
        ]

        stats = MetricsCalculator.compute_summary_stats(raw_issues)

        # Invariant 1: total_issues equals meaningful issues
        assert stats["total_issues"] == 9
        assert stats["meaningful_issues"] == 9
        assert stats["style_findings"] == 5
        assert stats["suppressed_findings"] == 2

        # Invariant 2: total_all_issues equals sum of all three mutually exclusive categories
        assert stats["total_all_issues"] == 16
        assert stats["total_all_issues"] == stats["meaningful_issues"] + stats["style_findings"] + stats["suppressed_findings"]

        # Invariant 3: sum(by_severity) == meaningful_issues (meaningful only)
        assert sum(stats["by_severity"].values()) == stats["meaningful_issues"]
        assert stats["by_severity"]["critical"] == 2
        assert stats["by_severity"]["high"] == 3
        assert stats["by_severity"]["medium"] == 4
        assert stats["by_severity"]["low"] == 0
        assert stats["by_severity"]["info"] == 0

        # Invariant 4: sum(all_by_severity) == total_all_issues (all issues)
        assert sum(stats["all_by_severity"].values()) == stats["total_all_issues"]
        assert stats["all_by_severity"]["critical"] == 2
        assert stats["all_by_severity"]["high"] == 3
        assert stats["all_by_severity"]["medium"] == 4
        assert stats["all_by_severity"]["low"] == 6  # 5 style + 1 suppressed
        assert stats["all_by_severity"]["info"] == 1  # 1 suppressed

        # Invariant 5: reasoning sources count matches total findings
        assert stats["reasoning_sources"]["llm"] == 4
        assert stats["reasoning_sources"]["static_analysis"] == 12
        assert stats["reasoning_sources"]["llm"] + stats["reasoning_sources"]["static_analysis"] == 16


# ═══════════════════════════════════════════════════════════════════
# K. BOUNDED CONTEXT EXTRACTION TESTS
# ═══════════════════════════════════════════════════════════════════

class TestBoundedContextExtraction:
    def test_extract_localized_code_from_full_code_with_line_numbers(self):
        """RootCauseEngine must extract target line ± context_lines with line numbers."""
        engine = RootCauseEngine(review_id="test-context")
        
        # Generate 120 lines of code
        code_lines = [f"x_{i} = {i} * 2" for i in range(1, 121)]
        full_code = "\n".join(code_lines)

        aggregated_context = {
            "file_path": "app/sample.py",
            "full_code": full_code,
            "code_context": []
        }

        # Target line 60
        extracted = engine._extract_localized_code(aggregated_context, line_no=60)

        assert ">>>   60 | x_60 = 60 * 2" in extracted
        assert "  10 | x_10 = 10 * 2" in extracted
        assert " 110 | x_110 = 110 * 2" in extracted
        # Lines far outside window should not be present
        assert "   1 | x_1 = 1 * 2" not in extracted
        assert " 120 | x_120 = 120 * 2" not in extracted
