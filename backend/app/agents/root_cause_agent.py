from typing import Dict, Any
import json
from app.llm.llm_client import LLMClient
from app.llm.prompts import ROOT_CAUSE_SYSTEM_PROMPT
from app.llm.response_parser import LLMResponseParser

class RootCauseAgent:
    def __init__(self, review_id: str):
        self.llm_client = LLMClient(review_id=review_id)
        
    def analyze(self, issue: Dict[str, Any], context: Dict[str, Any]) -> str:
        payload = {
            "issue": issue,
            "file_context": context.get("file_path", "unknown"),
            "code_context": context.get("code_context", [])
        }
        user_content = json.dumps(payload, indent=2)
        response = self.llm_client.generate_structured(ROOT_CAUSE_SYSTEM_PROMPT, user_content)
        
        if response:
            return LLMResponseParser.parse_root_cause(response)
        return "Analysis failed."
