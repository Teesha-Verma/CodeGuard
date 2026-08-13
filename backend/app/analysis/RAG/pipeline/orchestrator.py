"""
Pipeline Orchestrator Module.
"""
import time
from typing import Any, List, Optional
from app.analysis.RAG.execution.runner import PipelineRunner
from app.analysis.RAG.workflow.events import PipelineEventBus, PipelineEvent, PipelineEventType
from app.analysis.RAG.integration.stages import (
    StaticAnalysisStage,
    RetrievalStage,
    PromptBuilderStage,
    LLMExecutionStage,
    ReviewMergeStage,
)


class PipelineOrchestrator:
    """
    Coordinates pipeline execution order (Static Analysis -> Retrieval -> Prompt Builder -> Groq LLM -> Review Merge).
    Manages PipelineEventBus emissions.
    """

    def __init__(self, runner: Optional[PipelineRunner] = None, event_bus: Optional[PipelineEventBus] = None):
        """Initialize with a pipeline runner and event bus."""
        self.runner = runner or PipelineRunner()
        self.event_bus = event_bus or PipelineEventBus()

    def run_pipeline(self, context: Any, stages: Optional[List[Any]] = None) -> Any:
        """
        Run the full RAG pipeline with event emissions.

        Args:
            context: PipelineContext instance.
            stages: Optional list of stages to run.

        Returns:
            Updated PipelineContext.
        """
        request_id = getattr(context, "request_id", "req_unknown")

        self.event_bus.emit(
            PipelineEvent(
                event_id=f"evt_start_{time.time()}",
                event_type=PipelineEventType.STARTED,
                timestamp=time.time(),
                stage_name="orchestrator",
                request_id=request_id,
                data={"status": "started"},
            )
        )

        if stages is None:
            # Default pipeline stages:
            # Static Analysis -> Retrieval -> Prompt Builder -> Groq LLM -> Review Merge
            stages = [
                StaticAnalysisStage(),
                RetrievalStage(),
                PromptBuilderStage(),
                LLMExecutionStage(mock_llm=True),
                ReviewMergeStage(),
            ]

        try:
            for stage in stages:
                stage_name = stage.__class__.__name__
                self.event_bus.emit(
                    PipelineEvent(
                        event_id=f"evt_stage_start_{time.time()}",
                        event_type=PipelineEventType.STAGE_STARTED,
                        timestamp=time.time(),
                        stage_name=stage_name,
                        request_id=request_id,
                        data={"stage": stage_name},
                    )
                )

                context = self.runner.run_stages(context, [stage])

                self.event_bus.emit(
                    PipelineEvent(
                        event_id=f"evt_stage_comp_{time.time()}",
                        event_type=PipelineEventType.STAGE_COMPLETED,
                        timestamp=time.time(),
                        stage_name=stage_name,
                        request_id=request_id,
                        data={"stage": stage_name},
                    )
                )

                if getattr(context, "cancelled", False) or getattr(context, "errors", None):
                    if getattr(context, "errors", None):
                        self.event_bus.emit(
                            PipelineEvent(
                                event_id=f"evt_failed_{time.time()}",
                                event_type=PipelineEventType.FAILED,
                                timestamp=time.time(),
                                stage_name=stage_name,
                                request_id=request_id,
                                data={"errors": context.errors},
                            )
                        )

            setattr(context, "execution_stage", "completed")
            self.event_bus.emit(
                PipelineEvent(
                    event_id=f"evt_completed_{time.time()}",
                    event_type=PipelineEventType.COMPLETED,
                    timestamp=time.time(),
                    stage_name="orchestrator",
                    request_id=request_id,
                    data={"status": "completed"},
                )
            )

        except Exception as e:
            if hasattr(context, "errors"):
                context.errors.append(str(e))
            self.event_bus.emit(
                PipelineEvent(
                    event_id=f"evt_failed_{time.time()}",
                    event_type=PipelineEventType.FAILED,
                    timestamp=time.time(),
                    stage_name="orchestrator",
                    request_id=request_id,
                    data={"error": str(e)},
                )
            )

        return context
