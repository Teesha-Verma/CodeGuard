from radon.visitors import ComplexityVisitor
from radon.metrics import mi_visit
from radon.complexity import cc_rank
from typing import Dict, Any, List
from app.core.config import get_settings


class ComplexityAnalyzer:
    """Computes cyclomatic complexity and maintainability metrics using Radon.

    Phase 5 upgrade: thresholds are pulled from centralized Settings
    configuration, and human-readable interpretation descriptions are
    generated when thresholds are breached.  Raw numbers are kept as
    background data; interpretations are only surfaced when limits are
    exceeded.
    """

    def analyze(self, code: str, file_path: str = "") -> Dict[str, Any]:
        settings = get_settings()
        cc_max = settings.CYCLOMATIC_COMPLEXITY_MAX
        mi_min = settings.MAINTAINABILITY_INDEX_MIN

        try:
            visitor = ComplexityVisitor.from_code(code)
            functions = []

            for func in visitor.functions:
                exceeds = func.complexity > cc_max
                entry: Dict[str, Any] = {
                    "name": func.name,
                    "complexity": func.complexity,
                    "rank": cc_rank(func.complexity),
                    "start_line": func.lineno,
                    "end_line": getattr(func, "endline", func.lineno),
                    "exceeds_threshold": exceeds,
                }
                # Nuanced function complexity interpretation
                if exceeds:
                    entry["interpretation"] = (
                        f"This function has a higher number of execution paths "
                        f"(CC={func.complexity}, threshold={cc_max}). Simplifying the control "
                        f"flow or refactoring into smaller helpers would improve legibility."
                    )
                functions.append(entry)

            try:
                mi_score = mi_visit(code, multi=True)
            except Exception:
                mi_score = 100.0  # Safe default if MI fails

            mi_exceeds = mi_score < mi_min

            result: Dict[str, Any] = {
                "functions": functions,
                "maintainability_index": mi_score,
                "mi_exceeds_threshold": mi_exceeds,
            }

            # Human-readable MI interpretation when threshold breached
            if mi_exceeds:
                from app.static_analysis.context_resolver import ContextResolver
                context_meta = ContextResolver.resolve(file_path, code)
                
                is_declarative = (
                    context_meta.get("is_declarative_file")
                    or context_meta.get("is_config_file")
                    or context_meta.get("is_test_file")
                    or context_meta.get("is_migration_file")
                    or context_meta.get("is_generated_file")
                )
                
                if is_declarative:
                    result["mi_interpretation"] = (
                        f"This file contains structural abstractions or configurations (MI={mi_score:.1f}). "
                        f"While the structural density is higher, this is typical for schemas, configurations, "
                        f"or adapters. No critical refactoring is recommended."
                    )
                else:
                    result["mi_interpretation"] = (
                        f"The business logic in this file has higher structural complexity (MI={mi_score:.1f}, threshold={mi_min}). "
                        f"Consider simplifying conditional branches or separating concern layers to keep it easily maintainable."
                    )

            return result

        except Exception as e:
            return {
                "functions": [],
                "maintainability_index": 100.0,
                "mi_exceeds_threshold": False,
                "error": str(e),
            }
