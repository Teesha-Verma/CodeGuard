"""
Token management and budgeting modules for RAG.
"""
from typing import Dict
from pydantic import BaseModel, Field


class TokenBudget(BaseModel):
    """
    Configuration for token budget allocation.
    """
    max_prompt_tokens: int = Field(default=16000, description="Maximum total tokens allowed in the prompt")
    max_context_tokens: int = Field(default=10000, description="Maximum tokens allocated for context/retrieval")
    
    # Ratios for allocating the max_context_tokens
    system_ratio: float = Field(default=0.10, description="Ratio of budget for system instructions")
    critical_findings_ratio: float = Field(default=0.35, description="Ratio of budget for critical findings")
    retrieved_knowledge_ratio: float = Field(default=0.35, description="Ratio of budget for retrieved knowledge")
    examples_ratio: float = Field(default=0.10, description="Ratio of budget for examples")
    instructions_ratio: float = Field(default=0.10, description="Ratio of budget for specific instructions")


class TokenBudgetManager:
    """
    Manages token budgeting and text pruning.
    """

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Estimate the number of tokens in a string.
        (Rough approximation: 4 characters per token).
        
        Args:
            text (str): The text to estimate.
            
        Returns:
            int: Estimated number of tokens.
        """
        if not text:
            return 0
        return len(text) // 4

    @staticmethod
    def allocate_budget(total_budget: int) -> Dict[str, int]:
        """
        Allocate a total token budget into different sections based on default ratios.
        
        Args:
            total_budget (int): Total available tokens for context.
            
        Returns:
            dict[str, int]: Token allocation per section.
        """
        budget = TokenBudget()
        return {
            "system": int(total_budget * budget.system_ratio),
            "critical_findings": int(total_budget * budget.critical_findings_ratio),
            "retrieved_knowledge": int(total_budget * budget.retrieved_knowledge_ratio),
            "examples": int(total_budget * budget.examples_ratio),
            "instructions": int(total_budget * budget.instructions_ratio)
        }

    @classmethod
    def prune_text_to_budget(cls, text: str, max_tokens: int, preserve_header: bool = True) -> str:
        """
        Prune a string so it fits within a maximum token limit.
        
        Args:
            text (str): Text to prune.
            max_tokens (int): Maximum allowed tokens.
            preserve_header (bool): Attempt to preserve the first few lines if pruning is needed.
            
        Returns:
            str: Pruned text.
        """
        if cls.estimate_tokens(text) <= max_tokens:
            return text
            
        max_chars = max_tokens * 4
        
        if preserve_header and "\n" in text:
            # Simple approach: keep first line, trim from the end
            lines = text.split("\n")
            header = lines[0] + "\n"
            remaining_chars = max_chars - len(header) - 3 # -3 for "..."
            
            if remaining_chars > 0:
                body = "\n".join(lines[1:])
                return header + body[:remaining_chars] + "..."
            else:
                return text[:max_chars - 3] + "..."
                
        return text[:max_chars - 3] + "..."

    @classmethod
    def prune_sections(cls, sections: Dict[str, str], budget: TokenBudget) -> Dict[str, str]:
        """
        Prune multiple sections to fit their respective budgets.
        
        Args:
            sections (dict[str, str]): Dictionary of sections.
            budget (TokenBudget): TokenBudget configuration.
            
        Returns:
            dict[str, str]: Pruned sections.
        """
        allocations = cls.allocate_budget(budget.max_context_tokens)
        
        pruned = {}
        for section_name, text in sections.items():
            max_toks = allocations.get(section_name, budget.max_context_tokens)
            pruned[section_name] = cls.prune_text_to_budget(text, max_toks)
            
        return pruned
