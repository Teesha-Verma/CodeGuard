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
                "total_all_issues": 0,
                "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "all_by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
                "avg_meaningful_confidence": None,
                "avg_style_confidence": None,
                "detection_sources": {},
                "reasoning_sources": {},
                "evaluation_available": False
            }

        meaningful_count = 0
        style_count = 0
        suppressed_count = 0

        meaningful_total_conf = 0.0
        style_total_conf = 0.0

        # by_severity counts ONLY meaningful issues for consistency with total_issues
        meaningful_by_severity: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        # all_by_severity counts all issues for total_all_issues
        all_by_severity: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

        detection_sources: Dict[str, int] = {}
        reasoning_sources: Dict[str, int] = {}

        for issue in issues:
            conf = float(issue.get("confidence", 0.0))
            is_low = bool(issue.get("is_low_signal", False))
            
            # Map severity for this issue
            sev = issue.get("severity")
            if hasattr(sev, "value"):
                sev = sev.value
            sev = str(sev or "medium").lower()
            if sev not in all_by_severity:
                sev = "medium"

            # Classify into mutually exclusive categories
            if conf < 0.3:
                suppressed_count += 1
            elif is_low:
                style_count += 1
                style_total_conf += conf
            else:
                meaningful_count += 1
                meaningful_total_conf += conf
                # Count meaningful issues by severity
                meaningful_by_severity[sev] = meaningful_by_severity.get(sev, 0) + 1

            # Count ALL issues by severity
            all_by_severity[sev] = all_by_severity.get(sev, 0) + 1
                
            # Map separated detection and reasoning sources
            srcs = issue.get("sources", [])
            # Legacy fallback: singular 'source' field
            if not srcs and issue.get("source"):
                srcs = [issue["source"]]
            det_srcs = issue.get("detection_sources", [])
            reas_src = str(issue.get("reasoning_source") or "static_analysis").lower()
            
            # Legacy fallback if detection_sources not explicitly populated
            if not det_srcs:
                det_srcs = [s for s in srcs if str(s).lower() != reas_src]
                if not det_srcs and srcs:
                    det_srcs = srcs
            
            for d_src in det_srcs:
                d_key = str(d_src).lower()
                detection_sources[d_key] = detection_sources.get(d_key, 0) + 1
                
            reasoning_sources[reas_src] = reasoning_sources.get(reas_src, 0) + 1

        total_all = meaningful_count + style_count + suppressed_count
                
        avg_meaningful = round(meaningful_total_conf / meaningful_count, 2) if meaningful_count > 0 else None
        avg_style = round(style_total_conf / style_count, 2) if style_count > 0 else None
        
        return {
            # total_issues = meaningful only (backward compatibility)
            "total_issues": meaningful_count,
            "meaningful_issues": meaningful_count,
            "style_findings": style_count,
            "suppressed_findings": suppressed_count,
            # total_all_issues = sum of all three mutually exclusive categories
            "total_all_issues": total_all,
            # by_severity counts ONLY meaningful issues — sum(by_severity) == total_issues
            "by_severity": meaningful_by_severity,
            # all_by_severity counts ALL issues — sum(all_by_severity) == total_all_issues
            "all_by_severity": all_by_severity,
            "detection_sources": detection_sources,
            "reasoning_sources": reasoning_sources,
            "avg_meaningful_confidence": avg_meaningful,
            "avg_style_confidence": avg_style,
            "evaluation_available": True
        }
