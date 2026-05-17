from typing import Dict, Any, List, Optional
from app.core.constants import Severity, IssueType

class LLMResponseParser:
    """Parses and validates LLM JSON outputs."""
    
    @staticmethod
    def parse_bug_detection(raw_json: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parses the bug detection phase output."""
        issues = raw_json.get("issues", [])
        valid_issues = []
        for issue in issues:
            if "line" in issue and "issue" in issue:
                valid_issues.append({
                    "line": issue["line"],
                    "issue": issue["issue"],
                    "severity": issue.get("severity", Severity.MEDIUM),
                    "confidence": float(issue.get("confidence", 0.8)),
                    "issue_type": issue.get("issue_type", IssueType.BUG)
                })
        return valid_issues
        
    @staticmethod
    def parse_root_cause(raw_json: Dict[str, Any]) -> str:
        """Parses the root cause explanation."""
        return raw_json.get("root_cause_explanation", "Root cause explanation unavailable.")
        
    @staticmethod
    def parse_fix_suggestion(raw_json: Dict[str, Any]) -> Dict[str, str]:
        """Parses the fix suggestion and patch."""
        return {
            "fix": raw_json.get("fix_description", "No specific fix provided."),
            "patch": raw_json.get("patch", "")
        }
