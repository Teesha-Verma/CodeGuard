from typing import List, Dict, Any, Optional

class MetricsCalculator:
    """Calculates review-level statistics and evaluation metrics."""
    
    @staticmethod
    def compute_summary_stats(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not issues:
            return {
                "total_issues": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "by_source": {},
                "avg_confidence": None,
                "evaluation_available": False
            }

        stats: Dict[str, Any] = {
            "total_issues": len(issues),
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "by_source": {},
            "avg_confidence": 0.0,
            "evaluation_available": True
        }
        
        total_conf = 0.0
        for issue in issues:
            # Map severity
            sev = issue.get("severity")
            if hasattr(sev, "value"):
                sev = sev.value
            sev = str(sev or "medium").lower()
            
            if sev in stats["by_severity"]:
                stats["by_severity"][sev] += 1
            else:
                stats["by_severity"]["medium"] += 1
                
            # Map sources
            srcs = issue.get("sources", [])
            if not srcs and "source" in issue:
                old_src = issue["source"]
                if hasattr(old_src, "value"):
                    old_src = old_src.value
                srcs = [str(old_src)]
                
            for src in srcs:
                src_key = str(src).lower()
                stats["by_source"][src_key] = stats["by_source"].get(src_key, 0) + 1
                
            total_conf += float(issue.get("confidence", 0.0))
            
        stats["avg_confidence"] = round(total_conf / len(issues), 2)
        return stats

