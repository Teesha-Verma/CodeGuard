"""
Context Assembler module for RAG Phase 2.
"""

from typing import List, Set
from pydantic import BaseModel, Field
import hashlib

from app.analysis.RAG.search.result import DetailedSearchResult


class AssembledContext(BaseModel):
    """
    Data model for the finalized, assembled context ready for prompt insertion.
    """
    formatted_prompt_context: str = Field(
        ..., 
        description="Clean aggregated markdown with document titles, source paths, code patterns, recommendations"
    )
    retrieved_results: List[DetailedSearchResult] = Field(
        default_factory=list,
        description="The detailed search results that form this context"
    )
    total_documents: int = Field(
        ..., 
        description="Total number of unique documents assembled"
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of unique source paths or references"
    )


class ContextAssembler:
    """
    Assembles retrieval results into a cohesive format for LLM consumption.
    Handles duplicate snippet removal, relevance sorting, source attribution, and formatting.
    """

    def assemble_context(self, results: List[DetailedSearchResult], max_tokens_approx: int = 4000) -> AssembledContext:
        """
        Merges results, removes duplicate snippets, sorts by relevance, preserves source
        attributions, and formats the output into prompt-ready markdown context.
        
        Args:
            results: The reranked list of DetailedSearchResult.
            max_tokens_approx: A rough limit on the total characters/tokens for the context string.
            
        Returns:
            An AssembledContext object containing the formatted context and metadata.
        """
        if not results:
            return AssembledContext(
                formatted_prompt_context="No relevant context found.",
                retrieved_results=[],
                total_documents=0,
                sources=[]
            )
            
        # 1. Deduplicate snippets based on exact content
        unique_results = self._remove_duplicate_snippets(results)
        
        # 2. Sort by relevance (score) just to be sure it's descending
        unique_results.sort(key=lambda x: getattr(x, "score", 0.0), reverse=True)
        
        formatted_context_blocks = []
        sources: Set[str] = set()
        estimated_tokens = 0
        
        # 3. Format and assemble
        for res in unique_results:
            title = getattr(res, "title", "Untitled Context")
            source = getattr(res, "source_path", "Unknown Source")
            content = getattr(res, "content", "")
            
            # Additional context fields like patterns or recommendations if they exist
            metadata = getattr(res, "metadata", {})
            patterns = metadata.get("code_patterns", "")
            recommendations = metadata.get("recommendations", "")
            
            block = f"### Document: {title}\n"
            block += f"**Source**: `{source}`\n\n"
            block += f"{content}\n"
            
            if patterns:
                block += f"\n**Code Patterns**:\n{patterns}\n"
            if recommendations:
                block += f"\n**Recommendations**:\n{recommendations}\n"
                
            block += "\n---\n"
            
            # Rough token estimation (chars / 4 is a common rough heuristic)
            block_tokens = len(block) // 4
            
            if estimated_tokens + block_tokens > max_tokens_approx:
                break
                
            formatted_context_blocks.append(block)
            sources.add(source)
            estimated_tokens += block_tokens
            
        final_context = "\n".join(formatted_context_blocks)
        
        return AssembledContext(
            formatted_prompt_context=final_context.strip(),
            retrieved_results=unique_results[:len(formatted_context_blocks)],
            total_documents=len(formatted_context_blocks),
            sources=list(sources)
        )

    def _remove_duplicate_snippets(self, results: List[DetailedSearchResult]) -> List[DetailedSearchResult]:
        """Removes exact duplicate content blocks from the result list."""
        seen_hashes = set()
        unique = []
        
        for res in results:
            content = getattr(res, "content", "")
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(res)
                
        return unique
