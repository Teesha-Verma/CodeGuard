"""
Prioritization Engine for CodeGuard V2.

Tags findings with priority, category, and low-signal flags.
Ensures developer focus is prioritized on critical runtime/security errors,
and low-signal style findings never consume LLM budget.
"""

from typing import Dict, Any, Set
import re


class PrioritizationEngine:
    """
    Tags findings with priority, category, and low-signal flags.
    Ensures developer focus is prioritized on critical runtime/security errors.
    """

    # Low signal code mappings (Flake8, PyLint, pydocstyle, etc.)
    STYLE_CODES: Set[str] = {
        # Flake8 style / spacing / whitespace / blank lines
        "E501", "E301", "E302", "E303", "E304", "E305", "E306",
        "E201", "E202", "E203", "E221", "E222", "E225", "E226", "E231", "E241", "E251", "E261", "E262", "E265", "E271", "E272",
        "W291", "W292", "W293", "W391", "W503", "W504", "W191",
        "E101", "E111", "E114", "E115", "E116", "E121", "E122", "E123", "E124", "E125", "E126", "E127", "E128", "E129", "E131", "E133",
        "E701", "E702", "E703", "E704",
        # PyLint convention / formatting / docstring / naming
        "C0114", "C0115", "C0116", "C0103", "C0301", "C0302", "C0303", "C0304", "C0305", "C0325", "C0326", "C0330",
        "C0410", "C0411", "C0412", "C0413", "C0414", "C0415",
        "R0903", "R0913", "R0914", "R0915", "R0916", "R0902", "R0904",
        # pydocstyle docstring rules
        "D100", "D101", "D102", "D103", "D104", "D105", "D106", "D107",
        "D200", "D201", "D202", "D203", "D204", "D205", "D206", "D207", "D208", "D209", "D210", "D211", "D212", "D213",
        "D300", "D301", "D302",
        "D400", "D401", "D402", "D403", "D404", "D405", "D406", "D407", "D408", "D409", "D410", "D411", "D412", "D413", "D414", "D415",
    }

    # Style message substrings (case-insensitive)
    STYLE_MESSAGE_PATTERNS = [
        "trailing whitespace",
        "whitespace",
        "line too long",
        "line length",
        "missing docstring",
        "missing module docstring",
        "missing class docstring",
        "missing function or method docstring",
        "missing function docstring",
        "blank line contains whitespace",
        "too many blank lines",
        "expected 2 blank lines",
        "expected 1 blank line",
        "blank line",
        "trailing newline",
        "no newline at end of file",
        "bad-continuation",
        "invalid-name",
        "invalid name",
        "unnecessary-semicolon",
        "multiple-imports",
        "wrong-import-position",
        "wrong-import-order",
        "ungrouped-imports",
        "trailing-comma",
        "indentation",
        "formatting",
        "inline comment",
        "block comment",
        "too few public methods",
        "unused variable",
        "unused import",
    ]

    @staticmethod
    def is_style_rule(rule_id: str, message: str = "") -> bool:
        """Check if a rule ID or message corresponds to a cosmetic/style finding."""
        rule_upper = str(rule_id or "").upper().strip()
        msg_lower = str(message or "").lower().strip()

        if rule_upper in PrioritizationEngine.STYLE_CODES:
            return True

        for pattern in PrioritizationEngine.STYLE_MESSAGE_PATTERNS:
            if pattern in msg_lower:
                return True

        return False

    @staticmethod
    def analyze(
        source: str, 
        rule_id: str, 
        message: str = "", 
        context_meta: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Calculates prioritization and category tags for an issue finding.
        """
        rule_upper = str(rule_id or "").upper().strip()
        msg_lower = str(message or "").lower().strip()
        context_meta = context_meta or {
            "is_test_file": False,
            "is_config_file": False,
            "is_migration_file": False,
            "is_generated_file": False,
            "is_declarative_file": False,
        }

        # Defaults
        priority = "medium"
        category = "runtime logic risks"
        is_low_signal = False

        # ── 1. STYLE & COSMETIC RULES ───────────────────────────────────────
        if PrioritizationEngine.is_style_rule(rule_id, message):
            priority = "low"
            category = "style-only violations"
            is_low_signal = True

        # ── 1B. NESTING & COMPLEXITY ───────────────────────────────────────
        elif (
            rule_upper == "EXCESSIVE_NESTING"
            or "nesting" in msg_lower
            or "complexity" in msg_lower
            or "cyclomatic" in msg_lower
            or "maintainability" in msg_lower
        ):
            # Only escalate if nesting/complexity combines with branching explosion, recursion, mutation, or logic risk
            escalate = (
                "recursion" in msg_lower
                or "mutation" in msg_lower
                or "explosion" in msg_lower
                or "high complexity" in msg_lower
            )
            if escalate:
                priority = "medium"
                category = "runtime logic risks"
                is_low_signal = False
            else:
                priority = "low"
                category = "maintainability insights"
                is_low_signal = True

        # ── 2. SECURITY THREATS ──────────────────────────────────────────────
        elif (
            "security" in msg_lower 
            or "vulnerability" in msg_lower 
            or rule_upper.startswith("B")  # Bandit rules
            or "eval" in msg_lower 
            or "exec" in msg_lower 
            or "pickle" in msg_lower
            or "subprocess" in msg_lower
            or "sql injection" in msg_lower
            or "hardcoded password" in msg_lower
            or "taint" in msg_lower
            or "taint_flow" in rule_upper.lower()
        ):
            priority = "high"
            category = "security"
            is_low_signal = False

        # ── 3. AST OR RUNTIME RISKS ──────────────────────────────────────────
        elif (
            "mutation" in msg_lower 
            or "iterate" in msg_lower
            or "mutation" in rule_upper.lower()
            or "iterate" in rule_upper.lower()
            or rule_upper == "MUTATION_DURING_ITERATION"
            or rule_upper == "MUTATION"
        ):
            priority = "high"
            category = "mutation risks"
            is_low_signal = False

        elif (
            "async" in msg_lower 
            or "await" in msg_lower
            or "coroutine" in msg_lower
            or rule_upper == "ASYNC_MISUSE"
        ):
            priority = "high"
            category = "async misuse"
            is_low_signal = False

        elif (
            "variable_shadowing" in rule_upper 
            or "shadow" in msg_lower
        ):
            priority = "low"
            category = "style-only violations"
            is_low_signal = True

        elif (
            "global_modification" in rule_upper 
            or "global" in msg_lower
        ):
            priority = "medium"
            category = "runtime logic risks"
            is_low_signal = False

        # ── 4. CONTEXT OVERRIDES ─────────────────────────────────────────────
        if context_meta.get("is_test_file"):
            if rule_upper == "B101" or "assert" in msg_lower or "assertion" in msg_lower:
                priority = "low"
                category = "style-only violations"
                is_low_signal = True
            elif category != "security":
                priority = "low"
                if category == "runtime logic risks":
                    category = "style-only violations"

        if context_meta.get("is_config_file") or context_meta.get("is_migration_file") or context_meta.get("is_generated_file"):
            if category == "runtime logic risks":
                priority = "low"
                category = "style-only violations"
                is_low_signal = True

        if context_meta.get("is_declarative_file"):
            if category in ("runtime logic risks", "maintainability insights"):
                priority = "low"
                category = "maintainability insights"
                is_low_signal = True

        return {
            "signal_priority": priority,
            "issue_category": category,
            "is_low_signal": is_low_signal
        }
