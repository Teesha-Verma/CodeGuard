"""
RAG Pipeline Service Module.
"""
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.analysis.RAG.context.pipeline_context import PipelineContext
from app.analysis.RAG.pipeline.orchestrator import PipelineOrchestrator
from app.analysis.RAG.integration.stages import (
    StaticAnalysisStage,
    RetrievalStage,
    PromptBuilderStage,
    LLMExecutionStage,
    ReviewMergeStage,
)


class RAGPipelineConfig(BaseModel):
    """Configuration for the RAG Pipeline."""
    model_name: str = Field(default="gemini-3.6-flash")
    template_name: str = Field(default="mixed_review")
    output_format: str = Field(default="json")
    max_tokens: int = Field(default=16000)
    enable_cache: bool = Field(default=True)
    timeout_seconds: float = Field(default=120.0)
    mock_llm: bool = Field(default=True)


class RAGPipelineService:
    """Service class for RAG Pipeline."""

    def __init__(self, default_config: Optional[RAGPipelineConfig] = None):
        """Initialize with an optional default config."""
        self.default_config = default_config or RAGPipelineConfig()
        self.orchestrator = PipelineOrchestrator()

    def process_pull_request(
        self,
        pr_details: Dict[str, Any],
        static_findings: List[Dict[str, Any]],
        code_files: Optional[Dict[str, str]] = None,
        config: Optional[RAGPipelineConfig] = None
    ) -> Dict[str, Any]:
        """
        High-level interface to process a pull request through the RAG pipeline.

        Args:
            pr_details: Dictionary containing pull request metadata and details.
            static_findings: List of static analysis findings.
            code_files: Dictionary mapping file paths to their contents.
            config: Optional configuration overrides.

        Returns:
            Dictionary containing the pipeline results.
        """
        active_config = config or self.default_config
        req_id = pr_details.get("pr_id") or pr_details.get("id") or f"pr_{uuid.uuid4().hex[:8]}"

        repo_context = {
            "primary_language": pr_details.get("primary_language", "python"),
            "framework": pr_details.get("framework", ""),
            "repo_name": pr_details.get("repo_name", ""),
        }

        context = PipelineContext(
            request_id=str(req_id),
            pr_details=pr_details,
            repo_context=repo_context,
            analysis_findings=static_findings,
        )

        stages = [
            StaticAnalysisStage(),
            RetrievalStage(),
            PromptBuilderStage(),
            LLMExecutionStage(mock_llm=active_config.mock_llm),
            ReviewMergeStage(),
        ]

        result_context = self.orchestrator.run_pipeline(context, stages=stages)

        merged_dict = {}
        if result_context.merged_review:
            if hasattr(result_context.merged_review, "model_dump"):
                merged_dict = result_context.merged_review.model_dump()
            elif isinstance(result_context.merged_review, dict):
                merged_dict = result_context.merged_review

        return {
            "status": "success" if not result_context.errors else "partial_failure",
            "request_id": result_context.request_id,
            "execution_stage": result_context.execution_stage,
            "model_used": active_config.model_name,
            "mocked": active_config.mock_llm,
            "findings_processed": len(static_findings),
            "files_processed": len(code_files) if code_files else 0,
            "merged_review": merged_dict,
            "errors": result_context.errors,
        }
