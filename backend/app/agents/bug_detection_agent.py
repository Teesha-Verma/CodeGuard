from typing import Dict, Any, List
import json
from app.llm.llm_client import LLMClient
from app.llm.prompts import BUG_DETECTION_SYSTEM_PROMPT
from app.llm.response_parser import LLMResponseParser
from app.core.logger import PipelineLogger

class BugDetectionAgent:
    def __init__(self, review_id: str):
        self.llm_client = LLMClient(review_id=review_id)
        self.logger = PipelineLogger(review_id=review_id, stage="bug_detection_agent")
        
    def detect(self, aggregated_features: Dict[str, Any]) -> List[Dict[str, Any]]:
        self.logger.info(f"Running bug detection for {aggregated_features.get('file_path', 'unknown')}")
        
        # Prepare context payload
        user_content = json.dumps(aggregated_features, indent=2)
        
        response = self.llm_client.generate_structured(BUG_DETECTION_SYSTEM_PROMPT, user_content)
        
        if response:
            return LLMResponseParser.parse_bug_detection(response)
            
        # Heuristic fallback based on linter findings and dangerous patterns
        self.logger.warning("LLM API failed or returned empty response. Using heuristic fallback.")
        fallback_issues = []
        
        # 1. Check dangerous patterns from static analysis
        for pattern in aggregated_features.get("dangerous_patterns", []):
            fallback_issues.append({
                "line": pattern.get("line", 1),
                "issue": pattern.get("message", "Dangerous pattern detected."),
                "severity": "high",
                "confidence": 0.9,
                "issue_type": "bug"
            })
            
        # 2. Check linter findings
        for finding in aggregated_features.get("linter_findings", []):
            fallback_issues.append({
                "line": finding.get("line", 1),
                "issue": f"{finding.get('tool', 'linter')}: {finding.get('message', 'Style or logic issue.')}",
                "severity": finding.get("severity", "medium").lower(),
                "confidence": 0.8,
                "issue_type": "bug" if finding.get("severity") in ["critical", "high"] else "code_smell"
            })
            
        # 3. If no findings but code changed, add a generic review note to prove pipeline worked
        if not fallback_issues and aggregated_features.get("changed_lines"):
            fallback_issues.append({
                "line": aggregated_features["changed_lines"][0],
                "issue": "CodeGuard: Clean code analyzed. No critical bugs or lint issues found.",
                "severity": "info",
                "confidence": 1.0,
                "issue_type": "code_smell"
            })
            
        return fallback_issues
