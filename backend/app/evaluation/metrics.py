from typing import List, Dict, Any

class MetricsCalculator:
    """Calculates review-level statistics and evaluation metrics."""
    
    @staticmethod
    def compute_summary_stats(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        stats = {
            "total_issues": len(issues),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "by_source": {"llm": 0, "linter": 0},
            "avg_confidence": 0.0
        }
        
        if not issues:
            return stats
            
        total_conf = 0.0
        for issue in issues:
            sev = getattr(issue.get("severity"), "value", str(issue.get("severity", "medium")).lower())
            src = getattr(issue.get("source"), "value", str(issue.get("source", "llm")).lower())
            
            if sev in stats["by_severity"]:
                stats["by_severity"][sev] += 1
            if src in stats["by_source"]:
                stats["by_source"][src] += 1
                
            total_conf += float(issue.get("confidence", 0.0))
            
        stats["avg_confidence"] = round(total_conf / len(issues), 2)
        return stats
