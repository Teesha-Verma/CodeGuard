from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class DataFlowAdapter(BaseContextProvider):
    """
    Adapts raw Data Flow output into a RetrievalContextSignal.
    Does NOT compute dataflow, only adapts input dicts/objects.
    """

    def adapt(self, analysis_output: Any) -> RetrievalContextSignal:
        """Alias for extract_signal."""
        return self.extract_signal(analysis_output)

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from Data Flow output.
        Expects analysis_output to be a dict containing source-sink chains.
        """
        if not isinstance(analysis_output, dict):
            analysis_output = {}

        chains: List[Dict[str, Any]] = analysis_output.get("taint_chains", [])
        
        query_tokens = ["data_flow", "taint_analysis"]
        vulnerabilities = []
        severity = "INFO"

        single_source = analysis_output.get("source")
        single_sink = analysis_output.get("sink")
        single_taint = analysis_output.get("taint_type")

        if single_source:
            query_tokens.append(str(single_source))
        if single_sink:
            query_tokens.append(str(single_sink))
        if single_taint:
            vulnerabilities.append(str(single_taint))
            severity = "HIGH"
        
        for chain in chains:
            source = chain.get("source")
            sink = chain.get("sink")
            if source and sink:
                query_tokens.extend([str(source), str(sink)])
                vulnerabilities.append(f"tainted_flow_to_{sink}")
                severity = "CRITICAL"
                
        return RetrievalContextSignal(
            signal_type="data_flow",
            query_tokens=query_tokens,
            vulnerability_types=vulnerabilities,
            file_path=analysis_output.get("file_path", ""),
            severity=severity,
            metadata={"taint_chains": chains}
        )
