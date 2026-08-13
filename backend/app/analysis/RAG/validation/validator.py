"""
Prompt validation modules for RAG.
"""
import re
from typing import List
from pydantic import BaseModel, Field
from app.analysis.RAG.token_management.budget import TokenBudgetManager


class ValidationIssue(BaseModel):
    """
    Represents an issue found during prompt validation.
    """
    message: str
    severity: str = Field(pattern="^(error|warning)$")


class ValidationResult(BaseModel):
    """
    Result of a prompt validation pass.
    """
    is_valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    prompt_tokens: int = 0


class PromptValidator:
    """
    Validates prompts before sending them to the LLM.
    """

    @staticmethod
    def validate_prompt(system_instructions: str, user_prompt: str, max_tokens: int = 16000) -> ValidationResult:
        """
        Validate a complete prompt consisting of system instructions and user prompt.
        
        Args:
            system_instructions (str): The system prompt.
            user_prompt (str): The user prompt.
            max_tokens (int): Maximum allowed tokens.
            
        Returns:
            ValidationResult: The results of the validation.
        """
        result = ValidationResult()
        
        if not system_instructions or not system_instructions.strip():
            result.errors.append("System instructions cannot be empty.")
            result.is_valid = False
            
        if not user_prompt or not user_prompt.strip():
            result.errors.append("User prompt (context) cannot be empty.")
            result.is_valid = False
            
        total_text = f"{system_instructions}\n\n{user_prompt}"
        estimated_tokens = TokenBudgetManager.estimate_tokens(total_text)
        result.prompt_tokens = estimated_tokens
        
        if estimated_tokens > max_tokens:
            result.errors.append(f"Prompt length ({estimated_tokens} tokens) exceeds maximum limit ({max_tokens} tokens).")
            result.is_valid = False
            
        # Check for unformatted code blocks (loose indicators)
        if "```" in total_text:
            code_blocks = total_text.count("```")
            if code_blocks % 2 != 0:
                result.warnings.append("Mismatched or unclosed markdown code blocks detected.")
                
        # Check for broken links (e.g. empty brackets or missing parentheses)
        # Very simple regex for broken markdown links
        if re.search(r'\[\]\(|\)\[|\[[^\]]*\]\(\s*\)', total_text):
            result.warnings.append("Potentially broken markdown links detected.")
            
        return result
