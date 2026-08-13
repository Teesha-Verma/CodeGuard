from abc import ABC, abstractmethod
from typing import Any, Dict, List
from pydantic import BaseModel, Field

class RetrievalContextSignal(BaseModel):
    """
    Represents the unified signal structure extracted from various analysis sources.
    This signal is used to guide the RAG retrieval process.
    """
    signal_type: str = Field(..., description="Type of the signal (e.g., ast, cfg, call_graph, data_flow, repo_intel, linter, etc.)")
    query_tokens: List[str] = Field(default_factory=list, description="Keywords or tokens for the RAG query.")
    vulnerability_types: List[str] = Field(default_factory=list, description="Potential vulnerability types identified.")
    languages: List[str] = Field(default_factory=list, description="Programming languages involved.")
    frameworks: List[str] = Field(default_factory=list, description="Frameworks detected or related.")
    databases: List[str] = Field(default_factory=list, description="Databases detected or related.")
    orms: List[str] = Field(default_factory=list, description="ORMs detected or related.")
    file_path: str = Field(default="", description="Path to the file associated with this signal.")
    severity: str = Field(default="INFO", description="Severity level of the finding (INFO, WARNING, ERROR, CRITICAL).")
    tags: List[str] = Field(default_factory=list, description="Additional contextual tags.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata from the source.")

class BaseContextProvider(ABC):
    """
    Abstract base class for all context providers and adapters.
    """

    @abstractmethod
    def extract_signal(self, analysis_output: Any) -> RetrievalContextSignal:
        """
        Transforms the raw analysis output into a RetrievalContextSignal.

        Args:
            analysis_output (Any): The raw output from an analysis module.

        Returns:
            RetrievalContextSignal: The standardized context signal.
        """
        pass
