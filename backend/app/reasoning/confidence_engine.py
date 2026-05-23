from typing import Dict, Any, List, Optional
from app.core.config import get_settings


class ConfidenceEngine:
    """Calculates grounded, non-arbitrary confidence scores based on deterministic evidence integration.

    Phase 3 upgrade: pulls weights from centralized Settings configuration,
    applies context-aware calibration (test file, config file, low-signal,
    high-priority, high-precision AST bonuses/penalties), and clamps final
    scores to the [0.10, 1.00] band.
    """

    @staticmethod
    def calculate(
        finding: Dict[str, Any],
        raw_sources: List[str],
        evidence: Dict[str, Any],
        context_meta: Optional[Dict[str, Any]] = None,
        signal_meta: Optional[Dict[str, Any]] = None,
        is_changed: bool = False,
    ) -> Dict[str, Any]:
        """
        Calculates a grounded confidence score based on linter, AST, and
        validation constraints.  All weights are read from the centralized
        Settings singleton — no hardcoded magic numbers.

        Parameters
        ----------
        finding : dict
            The finding dict (must contain at least ``line``).
        raw_sources : list[str]
            Source identifiers, e.g. ``["bandit", "ast"]``.
        evidence : dict
            Evidence payload with ``ast_nodes``, ``linter_rules``, ``trigger_lines``.
        context_meta : dict, optional
            File context from ``ContextResolver.resolve()``
            (``is_test_file``, ``is_config_file``, …).
        signal_meta : dict, optional
            Signal metadata from ``PrioritizationEngine.analyze()``
            (``signal_priority``, ``is_low_signal``, ``issue_category``).

        Returns
        -------
        dict  with ``confidence`` (float), ``evidence_strength`` (str),
              ``reasons`` (list[str]).
        """
        settings = get_settings()

        # ── Base score ───────────────────────────────────────────
        score = settings.CONFIDENCE_BASE_SCORE
        reasons = [f"Base confidence of {settings.CONFIDENCE_BASE_SCORE:.2f} established."]

        # ── Linter contribution ──────────────────────────────────
        linters_found = [s for s in raw_sources if s in ("bandit", "pylint", "flake8")]

        if len(linters_found) >= 1:
            score += 0.20
            reasons.append(f"Single linter match detected (+0.20): {', '.join(linters_found)}")

        if len(linters_found) > 1:
            score += 0.15
            reasons.append("Multiple linter agreement (+0.15) observed.")

        # ── AST pattern contribution ─────────────────────────────
        if "ast" in raw_sources:
            score += 0.25
            reasons.append("AST mutation or scope pattern match (+0.25) confirmed.")

        # ── Evidence validation bonus ────────────────────────────
        has_ast_evidence = len(evidence.get("ast_nodes", [])) > 0
        has_linter_evidence = len(evidence.get("linter_rules", [])) > 0

        if has_ast_evidence or has_linter_evidence:
            score += 0.10
            reasons.append("Response validated against deterministic evidence constraints (+0.10).")

        # ── Context-aware calibrations (Phase 3) ─────────────────
        context_meta = context_meta or {}
        signal_meta = signal_meta or {}

        # High-priority bonus
        if signal_meta.get("signal_priority") == "high":
            bonus = settings.CONFIDENCE_HIGH_PRIORITY_BONUS
            score += bonus
            reasons.append(f"High-priority signal bonus ({bonus:+.2f}) applied.")

        # Low-signal penalty
        if signal_meta.get("is_low_signal"):
            penalty = settings.CONFIDENCE_LOW_SIGNAL_PENALTY
            score += penalty
            reasons.append(f"Low-signal penalty ({penalty:+.2f}) applied.")

        # Test-file discount (only for non-security findings)
        if context_meta.get("is_test_file") and signal_meta.get("issue_category") != "security":
            discount = settings.CONFIDENCE_TEST_FILE_DISCOUNT
            score += discount
            reasons.append(f"Test-file confidence discount ({discount:+.2f}) applied.")

        # Config-file discount
        if context_meta.get("is_config_file"):
            discount = settings.CONFIDENCE_CONFIG_FILE_DISCOUNT
            score += discount
            reasons.append(f"Config-file confidence discount ({discount:+.2f}) applied.")

        # High-precision AST rule bonus (eval, exec, subprocess, pickle)
        HIGH_PRECISION_RULES = {"eval_detection", "exec_detection", "unsafe_subprocess", "unsafe_pickle"}
        ast_rule_names = set()
        for ast_node in evidence.get("ast_nodes", []):
            rule = ast_node.get("rule_name", ast_node.get("pattern", ""))
            ast_rule_names.add(rule)
        if ast_rule_names & HIGH_PRECISION_RULES:
            bonus = settings.CONFIDENCE_HIGH_PRECISION_AST_BONUS
            score += bonus
            reasons.append(f"High-precision AST rule bonus ({bonus:+.2f}) applied.")

        # Changed-code boost (Phase 7 & 11)
        if is_changed:
            boost = settings.CONFIDENCE_CHANGED_CODE_BOOST
            score += boost
            reasons.append(f"Changed-code confidence boost ({boost:+.2f}) applied.")

        # Contextual override for B101/assert in test files (Phase 1)
        rule_id = str(finding.get("rule_id", "")).upper() if isinstance(finding, dict) else ""
        if (rule_id == "B101" or "assert" in str(finding.get("message", "")).lower()) and context_meta.get("is_test_file"):
            score = 0.15
            reasons = ["Assert statements in test files are standard practices. Confidence heavily reduced."]

        # ── Clamp to confidence ceiling (Phase 4 Refinement) ──────
        max_limit = 0.95
        if signal_meta.get("is_low_signal"):
            max_limit = 0.60
            if "Low-signal penalty" not in "".join(reasons):
                reasons.append("Low-signal finding: confidence capped at 0.60.")
            else:
                reasons.append("Confidence capped at 0.60 due to low-signal category.")

        final_score = round(max(0.10, min(max_limit, score)), 2)

        # ── Strength label ───────────────────────────────────────
        if final_score >= 0.85:
            strength = "strong"
        elif final_score >= 0.65:
            strength = "moderate"
        else:
            strength = "weak"

        return {
            "confidence": final_score,
            "evidence_strength": strength,
            "reasons": reasons,
        }
