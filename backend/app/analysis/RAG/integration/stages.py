from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List

from app.analysis.RAG.context.pipeline_context import PipelineContext
from app.analysis.RAG.context.ast_provider import ASTContextProvider
from app.analysis.RAG.context.cfg_provider import CFGContextProvider
from app.analysis.RAG.context.call_graph_provider import CallGraphContextProvider
from app.analysis.RAG.context.linter_provider import LinterContextProvider
from app.analysis.RAG.context.data_flow_adapter import DataFlowAdapter
from app.analysis.RAG.context.repo_intelligence_adapter import RepoIntelligenceAdapter
from app.analysis.RAG.query_builder.builder import QueryBuilder
from app.analysis.RAG.retrieval.engine import RetrievalEngine
from app.analysis.RAG.context.assembler import ContextAssembler
from app.analysis.RAG.prompt_builder.builder import PromptBuilder
from app.analysis.RAG.llm.mock_client import MockGroqClient, MockGeminiClient
from app.analysis.RAG.llm.groq_client import GroqClient
from app.analysis.RAG.review.merger import ReviewMerger


class BasePipelineStage(ABC):
    """
    Abstract base class for all RAG pipeline stages.
    """

    @abstractmethod
    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Executes the pipeline stage.
        """
        pass


class StaticAnalysisStage(BasePipelineStage):
    """
    Extracts context signals from AST, CFG, CallGraph, DataFlow, RepoIntel, Linter.
    """

    def __init__(self):
        self.ast_provider = ASTContextProvider()
        self.cfg_provider = CFGContextProvider()
        self.call_graph_provider = CallGraphContextProvider()
        self.linter_provider = LinterContextProvider()
        self.data_flow_adapter = DataFlowAdapter()
        self.repo_intel_adapter = RepoIntelligenceAdapter()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Executes static analysis signal extraction.
        """
        signals = []

        # Process repo intelligence signal
        if context.repo_context:
            signals.append(self.repo_intel_adapter.adapt(context.repo_context))

        # Extract signals from findings
        for finding in context.analysis_findings:
            category = str(finding.get("category", "")).lower()
            if "ast" in category or "syntax" in category:
                signals.append(self.ast_provider.extract_signal(finding))
            elif "cfg" in category or "control" in category:
                signals.append(self.cfg_provider.extract_signal(finding))
            elif "call" in category:
                signals.append(self.call_graph_provider.extract_signal(finding))
            elif "lint" in category:
                signals.append(self.linter_provider.extract_signal(finding))
            elif "flow" in category or "taint" in category:
                signals.append(self.data_flow_adapter.adapt(finding))
            else:
                # Default AST signal for generic findings
                signals.append(self.ast_provider.extract_signal(finding))

        # Default fallback signal if empty
        if not signals:
            signals.append(self.ast_provider.extract_signal({"vulnerability_types": ["code_review"]}))

        context.context_signals = signals
        context.execution_stage = "static_analysis"
        return context


class RetrievalStage(BasePipelineStage):
    """
    Runs query builder, similarity search, reranker, and context assembler.
    """

    def __init__(self, retrieval_engine: Optional[RetrievalEngine] = None):
        self.query_builder = QueryBuilder()
        if retrieval_engine is None:
            from app.analysis.RAG.embeddings.mock_provider import MockEmbeddingProvider
            from app.analysis.RAG.embeddings.service import EmbeddingService
            from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore
            emb_service = EmbeddingService(provider=MockEmbeddingProvider())
            v_store = InMemoryVectorStore()
            retrieval_engine = RetrievalEngine(embedding_service=emb_service, vector_store=v_store)

        self.retrieval_engine = retrieval_engine
        self.assembler = ContextAssembler()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Retrieves relevant context based on queries built from static analysis.
        """
        if context.context_signals:
            query = self.query_builder.build_query(context.context_signals)
            context.retrieval_query = query
            results = self.retrieval_engine.search(query, top_k=5)
            context.assembled_context = self.assembler.assemble_context(results)

        context.execution_stage = "retrieval"
        return context


class PromptBuilderStage(BasePipelineStage):
    """
    Uses PromptBuilder to prioritize context, select examples, format and validate prompt.
    """

    def __init__(self):
        self.prompt_builder = PromptBuilder()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Constructs and validates the prompt to be sent to the LLM.
        """
        final_prompt = self.prompt_builder.build_prompt(
            analysis_findings=context.analysis_findings,
            retrieved_context=context.assembled_context,
            repo_context=context.repo_context,
        )
        context.final_prompt = final_prompt
        context.execution_stage = "prompt_builder"
        return context


class LLMExecutionStage(BasePipelineStage):
    """
    Executes GroqClient/MockGroqClient with retry logic and caching.
    """

    def __init__(self, mock_llm: bool = True):
        self.mock_llm = mock_llm
        if mock_llm:
            self.client = MockGroqClient()
        else:
            self.client = GroqClient()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Invokes the LLM to get code review insights.
        """
        prompt_text = context.final_prompt.user_prompt if context.final_prompt else "Review code findings."
        sys_instruction = context.final_prompt.system_instruction if context.final_prompt else ""

        review_res = self.client.generate_review(prompt_text)
        context.structured_review = review_res
        context.execution_stage = "llm_execution"
        return context


class ReviewMergeStage(BasePipelineStage):
    """
    Calls ReviewMerger to combine static findings and LLM reasoning.
    """

    def __init__(self):
        self.merger = ReviewMerger()

    def execute(self, context: PipelineContext) -> PipelineContext:
        """
        Merges findings from static analysis and LLM execution.
        """
        merged = self.merger.merge_reviews(
            static_findings=context.analysis_findings,
            llm_review=context.structured_review,
            retrieved_context=context.assembled_context,
        )
        context.merged_review = merged
        context.execution_stage = "review_merged"
        return context
