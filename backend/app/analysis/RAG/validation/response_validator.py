import json
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

class ResponseValidationResult(BaseModel):
    """Result of validating an LLM response."""
    is_valid: bool = Field(default=False, description="Whether the response is valid")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    parsed_response: Any = Field(default=None, description="The parsed response object if valid")

class ResponseValidator:
    """Validates responses from the LLM."""
    
    VALID_SEVERITIES = {"critical", "high", "medium", "low", "info"}

    def validate_json_string(self, raw_text: str) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """
        Validate that the raw text is valid JSON.
        
        Args:
            raw_text: The raw string response from the LLM.
            
        Returns:
            A tuple of (is_valid, parsed_json, errors).
        """
        errors = []
        try:
            # Basic cleanup in case the LLM wrapped it in markdown
            text_to_parse = raw_text.strip()
            if text_to_parse.startswith("```json"):
                text_to_parse = text_to_parse[7:]
            if text_to_parse.startswith("```"):
                text_to_parse = text_to_parse[3:]
            if text_to_parse.endswith("```"):
                text_to_parse = text_to_parse[:-3]
            
            parsed = json.loads(text_to_parse.strip())
            return True, parsed, errors
        except json.JSONDecodeError as e:
            errors.append(f"Failed to parse JSON: {str(e)}")
            return False, None, errors
        except Exception as e:
            errors.append(f"Unexpected error during JSON parsing: {str(e)}")
            return False, None, errors

    def validate_review_object(self, review: Any) -> ResponseValidationResult:
        """
        Validate the structure and contents of a review object.
        
        Args:
            review: The parsed JSON object to validate.
            
        Returns:
            ResponseValidationResult containing validation status, errors, and warnings.
        """
        result = ResponseValidationResult()
        
        if not isinstance(review, dict):
            result.errors.append("Review object must be a dictionary.")
            return result
            
        if "issues" not in review:
            result.errors.append("Missing required field: 'issues'")
        elif not isinstance(review["issues"], list):
            result.errors.append("Field 'issues' must be a list.")
        else:
            for i, issue in enumerate(review["issues"]):
                if not isinstance(issue, dict):
                    result.errors.append(f"Issue at index {i} is not a dictionary.")
                    continue
                    
                severity = issue.get("severity")
                if not severity:
                    result.errors.append(f"Issue at index {i} missing required field 'severity'.")
                elif severity.lower() not in self.VALID_SEVERITIES:
                    result.errors.append(f"Issue at index {i} has invalid severity '{severity}'. Valid options are: {', '.join(self.VALID_SEVERITIES)}")
                
                confidence = issue.get("confidence")
                if confidence is not None:
                    if not isinstance(confidence, (int, float)):
                        result.errors.append(f"Issue at index {i} has non-numeric confidence.")
                    elif not (0.0 <= confidence <= 1.0):
                        result.errors.append(f"Issue at index {i} confidence {confidence} is out of range [0.0, 1.0].")
                        
        result.is_valid = len(result.errors) == 0
        if result.is_valid:
            result.parsed_response = review
            
        return result
