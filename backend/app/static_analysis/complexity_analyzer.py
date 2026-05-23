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

    def analyze(self, code: str) -> Dict[str, Any]:
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
                # Phase 5: human-readable interpretation when threshold breached
                if exceeds:
                    entry["interpretation"] = (
                        f"This function has high cyclomatic complexity "
                        f"(CC={func.complexity}, threshold={cc_max}), making it "
                        f"difficult to cover with unit tests. Suggest dividing it "
                        f"into smaller helpers."
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

            # Phase 5: human-readable MI interpretation when threshold breached (Phase 3 refinement)
            if mi_exceeds:
                result["mi_interpretation"] = (
                    f"This code has increased structural density and lower "
                    f"maintainability metrics (MI={mi_score:.1f}, threshold={mi_min}). "
                    f"Suggest simplifying nested structures or decomposing logic."
                )

            return result

        except Exception as e:
            return {
                "functions": [],
                "maintainability_index": 100.0,
                "mi_exceeds_threshold": False,
                "error": str(e),
            }
