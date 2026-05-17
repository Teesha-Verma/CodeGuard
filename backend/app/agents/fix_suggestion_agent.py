from typing import Dict, Any
import json
from app.llm.llm_client import LLMClient
from app.llm.prompts import FIX_SUGGESTION_SYSTEM_PROMPT
from app.llm.response_parser import LLMResponseParser

class FixSuggestionAgent:
    def __init__(self, review_id: str):
        self.llm_client = LLMClient(review_id=review_id)
        
    def suggest(self, issue: Dict[str, Any], root_cause: str, context: Dict[str, Any]) -> Dict[str, str]:
        payload = {
            "issue": issue,
            "root_cause": root_cause,
            "file_context": context.get("file_path", "unknown"),
            "code_context": context.get("code_context", [])
        }
        user_content = json.dumps(payload, indent=2)
        response = self.llm_client.generate_structured(FIX_SUGGESTION_SYSTEM_PROMPT, user_content)
        
        if response:
            return LLMResponseParser.parse_fix_suggestion(response)
        return {"fix": "No fix available.", "patch": ""}
