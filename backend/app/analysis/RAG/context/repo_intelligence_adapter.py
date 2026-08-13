from typing import Any, Dict, List
from .base import BaseContextProvider, RetrievalContextSignal

class RepoIntelligenceAdapter(BaseContextProvider):
    """
    Adapts Repository Intelligence metadata into a RetrievalContextSignal.
    Does NOT compute repo intel, only adapts input context.
    """

    def adapt(self, analysis_output: Any) -> RetrievalContextSignal:
        """Alias for extract_signal."""
        return self.extract_signal(analysis_output)

    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Extracts signal from Repo Intelligence.
        Expects analysis_output to be a dict containing repo metadata.
        """
        if not isinstance(analysis_output, dict):
            analysis_output = {}

        languages: List[str] = list(analysis_output.get("languages", []) or [])
        if not languages:
            lang = analysis_output.get("primary_language") or analysis_output.get("language")
            if lang:
                languages = [str(lang)]

        frameworks: List[str] = list(analysis_output.get("frameworks", []) or [])
        if not frameworks and analysis_output.get("framework"):
            frameworks = [str(analysis_output["framework"])]

        databases: List[str] = list(analysis_output.get("databases", []) or [])
        if not databases and analysis_output.get("database"):
            databases = [str(analysis_output["database"])]

        orms: List[str] = list(analysis_output.get("orms", []) or [])
        if not orms and analysis_output.get("orm"):
            orms = [str(analysis_output["orm"])]
        
        query_tokens = ["repo_intelligence"]
        query_tokens.extend(frameworks)
        query_tokens.extend(databases)
        query_tokens.extend(orms)

        return RetrievalContextSignal(
            signal_type="repo_intel",
            query_tokens=query_tokens,
            languages=languages,
            frameworks=frameworks,
            databases=databases,
            orms=orms,
            file_path=analysis_output.get("file_path", ""),
            severity="INFO",
            metadata={"architecture_style": analysis_output.get("architecture_style", "")}
        )
