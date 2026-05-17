from radon.visitors import ComplexityVisitor
from radon.metrics import mi_visit
from typing import Dict, Any, List

class ComplexityAnalyzer:
    """Computes cyclomatic complexity and maintainability metrics using Radon."""
    
    def analyze(self, code: str) -> Dict[str, Any]:
        try:
            visitor = ComplexityVisitor.from_code(code)
            functions = []
            
            for func in visitor.functions:
                functions.append({
                    "name": func.name,
                    "complexity": func.complexity,
                    "rank": func.rank,
                    "start_line": func.lineno,
                    "end_line": getattr(func, 'endline', func.lineno)
                })
                
            mi_score = mi_visit(code, multi=True)
            
            return {
                "functions": functions,
                "maintainability_index": mi_score
            }
        except Exception as e:
            return {"error": str(e)}
