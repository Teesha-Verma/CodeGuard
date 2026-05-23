from typing import Dict, Any

class PrioritizationEngine:
    """
    Tags findings with priority, category, and low-signal flags.
    Ensures developer focus is prioritized on critical runtime/security errors.
    """

    # Low signal code mappings (Flake8 & PyLint)
    STYLE_CODES = {
        # Flake8 style / spacing
        "E501", "E301", "E302", "E303", "E305", "E201", "E202", "E203", "E221", "E225", "E251", "E261", "E265",
        "W291", "W292", "W293", "W391", "W503", "W504",
        # PyLint convention / formatting
        "C0114", "C0115", "C0116", "C0103", "C0301", "C0303", "C0325", "C0326", "C0304", "C0305", "R0903"
    }

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
        rule_upper = str(rule_id).upper()
        msg_lower = str(message).lower()
        context_meta = context_meta or {
            "is_test_file": False,
            "is_config_file": False,
            "is_migration_file": False,
            "is_generated_file": False
        }

        # Defaults
        priority = "medium"
        category = "runtime logic risks"
        is_low_signal = False

        # ── 1. STYLE & COSMETIC RULES ───────────────────────────────────────
        if (
            rule_upper in PrioritizationEngine.STYLE_CODES 
            or "line too long" in msg_lower 
            or "whitespace" in msg_lower 
            or "missing docstring" in msg_lower
            or "indentation" in msg_lower
            or "formatting" in msg_lower
        ):
            priority = "low"
            category = "style-only violations"
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

        return {
            "signal_priority": priority,
            "issue_category": category,
            "is_low_signal": is_low_signal
        }
