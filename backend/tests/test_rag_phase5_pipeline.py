"""Unit and integration tests for Phase 5: RAG Pipeline Integration in app.analysis.RAG."""

import pytest
from app.analysis.RAG.context.pipeline_context import PipelineContext
from app.analysis.RAG.workflow.events import PipelineEventBus, PipelineEventType, PipelineEvent
from app.analysis.RAG.review.merger import ReviewMerger, MergedReview
from app.analysis.RAG.integration.stages import (
    StaticAnalysisStage,
    RetrievalStage,
    PromptBuilderStage,
    LLMExecutionStage,
    ReviewMergeStage,
)
from app.analysis.RAG.execution.runner import PipelineRunner
from app.analysis.RAG.pipeline.orchestrator import PipelineOrchestrator
from app.analysis.RAG.services.rag_pipeline_service import RAGPipelineService, RAGPipelineConfig


class TestPipelineContextAndEvents:
    """Test PipelineContext model and PipelineEventBus."""

    def test_pipeline_context_initialization(self):
        ctx = PipelineContext(
            request_id="pr_101",
            pr_details={"title": "Fix SQL injection in auth endpoint", "author": "dev"},
            repo_context={"primary_language": "python", "framework": "fastapi"},
            analysis_findings=[{"title": "SQL Injection", "severity": "CRITICAL"}],
        )
        assert ctx.request_id == "pr_101"
        assert ctx.execution_stage == "initialized"
        assert len(ctx.analysis_findings) == 1
        assert ctx.cancelled is False

    def test_pipeline_event_bus(self):
        bus = PipelineEventBus()
        received_events = []

        def on_started(event: PipelineEvent):
            received_events.append(event)

        bus.subscribe(PipelineEventType.STARTED, on_started)
        evt = PipelineEvent(
            event_id="e1",
            event_type=PipelineEventType.STARTED,
            timestamp=1000.0,
            stage_name="orchestrator",
            request_id="pr_101",
            data={"status": "started"},
        )
        bus.emit(evt)
        assert len(received_events) == 1
        assert received_events[0].request_id == "pr_101"


class TestReviewMerger:
    """Test ReviewMerger combining static findings and LLM review."""

    def test_merge_reviews(self):
        merger = ReviewMerger()
        static_findings = [
            {"title": "Unused variable", "severity": "LOW", "category": "style", "confidence": 0.5},
            {"title": "SQL Injection", "severity": "CRITICAL", "category": "security", "confidence": 0.95},
        ]
        llm_review_dict = {
            "review_summary": "Found critical SQL Injection in auth query.",
            "overall_severity": "critical",
            "findings": [
                {
                    "title": "SQL Injection in execute()",
                    "severity": "critical",
                    "file_path": "app/db.py",
                    "evidence": "db.execute(query)",
                    "reasoning": "User input directly formatted into query.",
                    "remediation": "Use parameterized query.",
                }
            ],
            "confidence": 0.9,
            "priority": "high",
        }

        merged: MergedReview = merger.merge_reviews(static_findings, llm_review_dict)
        assert isinstance(merged, MergedReview)
        assert merged.overall_severity == "critical"
        assert merged.confidence_score >= 0.8
        assert len(merged.findings) >= 2


class TestPipelineStagesAndRunner:
    """Test individual pipeline stages and PipelineRunner."""

    def test_pipeline_stages_execution(self):
        ctx = PipelineContext(
            request_id="pr_202",
            pr_details={"title": "Update user API endpoint"},
            repo_context={"primary_language": "python", "framework": "fastapi"},
            analysis_findings=[{"title": "Eval usage", "severity": "CRITICAL", "category": "security"}],
        )

        static_stage = StaticAnalysisStage()
        ctx = static_stage.execute(ctx)
        assert len(ctx.context_signals) >= 1

        prompt_stage = PromptBuilderStage()
        ctx = prompt_stage.execute(ctx)
        assert ctx.final_prompt is not None

        llm_stage = LLMExecutionStage(mock_llm=True)
        ctx = llm_stage.execute(ctx)
        assert ctx.structured_review is not None

        merge_stage = ReviewMergeStage()
        ctx = merge_stage.execute(ctx)
        assert ctx.merged_review is not None
        assert ctx.execution_stage == "review_merged"

    def test_pipeline_runner(self):
        runner = PipelineRunner()
        ctx = PipelineContext(
            request_id="pr_303",
            repo_context={"primary_language": "python"},
            analysis_findings=[{"title": "High complexity", "severity": "MEDIUM"}],
        )
        stages = [StaticAnalysisStage(), PromptBuilderStage(), LLMExecutionStage(mock_llm=True)]
        res_ctx = runner.run_stages(ctx, stages)
        assert res_ctx.structured_review is not None


class TestPipelineOrchestratorAndService:
    """Test PipelineOrchestrator and end-to-end RAGPipelineService."""

    def test_orchestrator(self):
        orchestrator = PipelineOrchestrator()
        ctx = PipelineContext(
            request_id="pr_404",
            repo_context={"primary_language": "python", "framework": "fastapi"},
            analysis_findings=[{"title": "Insecure cookie", "severity": "HIGH"}],
        )
        res_ctx = orchestrator.run_pipeline(ctx)
        assert res_ctx.execution_stage in ("completed", "review_merged")
        assert res_ctx.merged_review is not None

    def test_rag_pipeline_service_end_to_end(self):
        service = RAGPipelineService()
        config = RAGPipelineConfig(
            model_name="gemini-2.5-flash",
            template_name="security_review",
            output_format="json",
            max_tokens=16000,
            mock_llm=True,
        )
        pr_details = {
            "pr_id": "123",
            "repo_name": "backend-auth-service",
            "primary_language": "python",
            "framework": "fastapi",
        }
        static_findings = [
            {
                "title": "SQL Injection vulnerability",
                "severity": "CRITICAL",
                "category": "security",
                "file": "app/auth.py",
                "line": 42,
            }
        ]

        result = service.process_pull_request(
            pr_details=pr_details,
            static_findings=static_findings,
            config=config,
        )

        assert isinstance(result, dict)
        assert result["status"] == "success"
        assert result["request_id"] is not None
        assert "merged_review" in result
        assert result["merged_review"]["overall_severity"] in ("critical", "high", "medium", "low", "info")
