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
        return []
