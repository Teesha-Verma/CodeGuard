from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class CallGraphContextProvider(BaseContextProvider):
    """
    Transforms Call Graph findings into a RetrievalContextSignal.
    """

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from Call Graph findings.
        Expects analysis_output to be a dict containing call chain depth,
        interprocedural calls, external API calls.
        """
        if not isinstance(analysis_output, dict):
            analysis_output = {}

        chain_depth: int = analysis_output.get("chain_depth", 0)
        external_apis: List[str] = analysis_output.get("external_apis", [])
        
        caller = analysis_output.get("caller")
        callee = analysis_output.get("callee")
        
        query_tokens = ["call_graph"]
        if caller:
            query_tokens.append(str(caller))
        if callee:
            query_tokens.append(str(callee))
        query_tokens.extend(external_apis)
        
        tags = []
        severity = "INFO"
        if chain_depth > 5:
            tags.append("deep_call_chain")
            
        if external_apis:
            tags.append("external_dependency")

        return RetrievalContextSignal(
            signal_type="call_graph",
            query_tokens=query_tokens,
            file_path=analysis_output.get("file_path", ""),
            severity=severity,
            tags=tags,
            metadata={
                "chain_depth": chain_depth,
                "external_apis": external_apis
            }
        )
