from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class CFGContextProvider(BaseContextProvider):
    """
    Transforms Control Flow Graph (CFG) findings into a RetrievalContextSignal.
    """

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from CFG findings.
        Expects analysis_output to be a dict containing loop complexity,
        unreachable blocks, and branch paths.
        """
        if not isinstance(analysis_output, dict):
            analysis_output = {}

        loop_complexity: int = analysis_output.get("loop_complexity", 0)
        cyclomatic_complexity: int = analysis_output.get("cyclomatic_complexity", 0)
        unreachable_blocks: int = analysis_output.get("unreachable_blocks", 0)
        
        query_tokens = ["control_flow", "branch"]
        if cyclomatic_complexity > 0:
            query_tokens.append(f"cyclomatic_complexity:{cyclomatic_complexity}")
        tags = []
        severity = "INFO"
        
        if loop_complexity > 10:
            tags.append("high_complexity")
            severity = "WARNING"
            
        if unreachable_blocks > 0:
            tags.append("dead_code")

        return RetrievalContextSignal(
            signal_type="cfg",
            query_tokens=query_tokens,
            file_path=analysis_output.get("file_path", ""),
            severity=severity,
            tags=tags,
            metadata={
                "loop_complexity": loop_complexity,
                "unreachable_blocks": unreachable_blocks
            }
        )
