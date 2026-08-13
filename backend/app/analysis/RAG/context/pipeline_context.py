from typing import Any
from pydantic import BaseModel, Field


class PipelineContext(BaseModel):
    """
    Context object that holds the state of the RAG pipeline execution.
    It carries all required data across different stages of the workflow.
    """
    request_id: str
    pr_details: dict[str, Any] = Field(default_factory=dict)
    repo_context: dict[str, Any] = Field(default_factory=dict)
    analysis_findings: list[dict[str, Any]] = Field(default_factory=list)
    context_signals: list[Any] = Field(default_factory=list)
    retrieval_query: Any = None
    assembled_context: Any = None
    final_prompt: Any = None
    llm_raw_response: str = ""
    structured_review: Any = None
    merged_review: Any = None
    execution_stage: str = "initialized"
    telemetry_metrics: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    cancelled: bool = False
