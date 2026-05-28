from typing import List, Dict, Any, Optional

class MetricsCalculator:
    """Calculates review-level statistics and evaluation metrics."""
    
    @staticmethod
    def compute_summary_stats(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not issues:
            return {
                "total_issues": 0,
                "meaningful_issues": 0,
                "style_findings": 0,
                "suppressed_findings": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "avg_meaningful_confidence": None,
                "avg_style_confidence": None,
                "evaluation_available": False
            }

        meaningful_count = 0
        style_count = 0
        suppressed_count = 0

        meaningful_total_conf = 0.0
        style_total_conf = 0.0

        for issue in issues:
            conf = float(issue.get("confidence", 0.0))
            is_low = bool(issue.get("is_low_signal", False))
            
            # Contextual or absolute low confidence constitutes a suppressed finding
            if conf < 0.3:
                suppressed_count += 1
            elif is_low:
                style_count += 1
                style_total_conf += conf
            else:
                meaningful_count += 1
                meaningful_total_conf += conf

        stats: Dict[str, Any] = {
            "total_issues": meaningful_count,  # NOT inflated! Only counts meaningful safety-critical issues
            "meaningful_issues": meaningful_count,
            "style_findings": style_count,
            "suppressed_findings": suppressed_count,
            "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
            "detection_sources": {},
            "reasoning_sources": {},
            "avg_meaningful_confidence": None,
            "avg_style_confidence": None,
            "evaluation_available": True
        }
        
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
                
            # Map sources (fallback compatibility)
            srcs = issue.get("sources", [])
            if not srcs and "source" in issue:
                old_src = issue["source"]
                if hasattr(old_src, "value"):
                    old_src = old_src.value
                srcs = [str(old_src)]
                
            # Map separated detection and reasoning sources
            det_srcs = issue.get("detection_sources", [])
            reas_src = str(issue.get("reasoning_source") or "static_analysis").lower()
            
            # Legacy fallback if detection_sources not explicitly populated in input dictionary
            if not det_srcs:
                det_srcs = [s for s in srcs if str(s).lower() != reas_src]
                # If still empty (e.g. source was "llm" or "static_analysis" only), keep it
                if not det_srcs and srcs:
                    det_srcs = srcs
            
            for d_src in det_srcs:
                d_key = str(d_src).lower()
                stats["detection_sources"][d_key] = stats["detection_sources"].get(d_key, 0) + 1
                
            stats["reasoning_sources"][reas_src] = stats["reasoning_sources"].get(reas_src, 0) + 1
                
        avg_meaningful = round(meaningful_total_conf / meaningful_count, 2) if meaningful_count > 0 else None
        avg_style = round(style_total_conf / style_count, 2) if style_count > 0 else None
        
        stats["avg_meaningful_confidence"] = avg_meaningful
        stats["avg_style_confidence"] = avg_style
        return stats

