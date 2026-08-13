from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class ASTContextProvider(BaseContextProvider):
    """
    Transforms Abstract Syntax Tree (AST) findings into a RetrievalContextSignal.
    """

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from AST findings.
        Expects analysis_output to be a dict containing node types, function names,
        and dangerous calls like eval, exec, etc.
        """
        if not isinstance(analysis_output, dict):
            analysis_output = {}

        node_types: List[str] = analysis_output.get("node_types", [])
        function_names: List[str] = analysis_output.get("function_names", [])
        dangerous_calls: List[str] = analysis_output.get("dangerous_calls", [])
        
        query_tokens = []
        query_tokens.extend(node_types)
        query_tokens.extend(function_names)
        query_tokens.extend(dangerous_calls)

        vulnerabilities = list(analysis_output.get("vulnerability_types", []) or [])
        severity = "INFO"
        if dangerous_calls:
            if "code_injection" not in vulnerabilities:
                vulnerabilities.append("code_injection")
            severity = "CRITICAL"

        return RetrievalContextSignal(
            signal_type="ast",
            query_tokens=query_tokens,
            vulnerability_types=vulnerabilities,
            file_path=analysis_output.get("file_path", ""),
            severity=severity,
            metadata={"dangerous_calls": dangerous_calls}
        )
