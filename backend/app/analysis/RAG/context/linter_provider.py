from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class LinterContextProvider(BaseContextProvider):
    """
    Transforms linter violations into a RetrievalContextSignal.
    """

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from linter findings.
        Expects analysis_output to be a dict containing linter codes and violations.
        """
        if isinstance(analysis_output, list):
            violations = analysis_output
            file_path = ""
        elif isinstance(analysis_output, dict):
            violations = analysis_output.get("violations", [])
            file_path = analysis_output.get("file_path", "")
        else:
            violations = []
            file_path = ""
        
        query_tokens = []
        vulnerabilities = []
        severity = "INFO"
        
        for v in violations:
            code = v.get("code", "")
            if code:
                query_tokens.append(code)
            
            # Security linter checks (e.g. Bandit B101-B799)
            if code.startswith("B"):
                vulnerabilities.append("security_linter_flag")
                severity = "WARNING"
                
        return RetrievalContextSignal(
            signal_type="linter",
            query_tokens=query_tokens,
            vulnerability_types=vulnerabilities,
            file_path=file_path,
            severity=severity,
            metadata={"violations_count": len(violations)}
        )
