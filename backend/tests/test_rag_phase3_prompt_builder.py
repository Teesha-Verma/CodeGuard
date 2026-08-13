"""Unit tests for Phase 3: Prompt Builder & Context Orchestration Layer in app.analysis.RAG."""

import pytest

from app.analysis.RAG.formatting.formatters import PromptFormatter
from app.analysis.RAG.token_management.budget import TokenBudgetManager, TokenBudget
from app.analysis.RAG.validation.validator import PromptValidator, ValidationResult
from app.analysis.RAG.context_management.prioritizer import ContextPrioritizer
from app.analysis.RAG.context_management.merger import ContextMerger, MergedContext
from app.analysis.RAG.examples.selector import ExampleSelector, ExampleItem
from app.analysis.RAG.templates.template_engine import TemplateEngine, PromptTemplate
from app.analysis.RAG.prompt_builder.builder import PromptBuilder, FinalPrompt
from app.analysis.RAG.search.result import DetailedSearchResult
from app.analysis.RAG.context.assembler import AssembledContext


class TestFormattingAndValidation:
    """Test formatting utilities and prompt validator."""

    def test_prompt_formatter(self):
        formatter = PromptFormatter()
        sec = formatter.format_section("Critical Findings", "Details here...", level=2)
        assert "## Critical Findings" in sec
        assert "Details here..." in sec

        code_blk = formatter.format_code_block("print('hello')", "python")
        assert "```python" in code_blk
        assert "print('hello')" in code_blk

        ref = formatter.format_reference("OWASP A01", "/path/a01.md", "L10-20")
        assert "OWASP A01" in ref
        assert "/path/a01.md" in ref

    def test_prompt_validator(self):
        validator = PromptValidator()
        res = validator.validate_prompt(
            system_instructions="You are a principal security engineer.",
            user_prompt="## Analysis Summary\nReview this code.\n\n## Output Format\nReturn JSON.",
            max_tokens=16000,
        )
        assert res.is_valid
        assert res.prompt_tokens > 0


class TestTokenManagement:
    """Test token budget manager."""

    def test_token_budget_estimation_and_pruning(self):
        manager = TokenBudgetManager()
        text = "a" * 400
        est = manager.estimate_tokens(text)
        assert est == 100

        long_text = "Line 1\nLine 2\nLine 3\n" * 500
        pruned = manager.prune_text_to_budget(long_text, max_tokens=100)
        assert manager.estimate_tokens(pruned) <= 120


class TestContextManagementAndPrioritizer:
    """Test context prioritizer, merger, and example selector."""

    def test_context_prioritizer(self):
        prioritizer = ContextPrioritizer()
        findings = [
            {"title": "Unused import", "severity": "LOW", "category": "style", "confidence": 0.5},
            {"title": "SQL Injection", "severity": "CRITICAL", "category": "security", "confidence": 0.95},
            {"title": "Missing docstring", "severity": "INFO", "category": "convention", "confidence": 0.4},
        ]
        sorted_findings = prioritizer.prioritize_findings(findings)
        assert sorted_findings[0]["title"] == "SQL Injection"

    def test_context_merger(self):
        merger = ContextMerger()
        findings = [
            {"title": "SQL Injection in endpoint", "severity": "CRITICAL", "category": "security"},
            {"title": "Inefficient loop", "severity": "MEDIUM", "category": "performance"},
        ]
        sr = DetailedSearchResult(
            chunk_id="c1",
            document_id="OWASP-A03",
            title="OWASP SQL Injection",
            content="Use parameterized queries to prevent SQL injection.",
            source_path="/kb/a03.md",
            similarity_score=0.9,
            raw_metadata={"category": "security"},
        )
        assembled = AssembledContext(
            formatted_prompt_context="## OWASP SQL Injection\nUse parameterized queries.",
            retrieved_results=[sr],
            total_documents=1,
            sources=["/kb/a03.md"],
        )
        repo_ctx = {
            "primary_language": "python",
            "framework": "fastapi",
            "architecture_style": "clean_architecture",
        }

        merged = merger.merge_all(findings, assembled, repo_ctx)
        assert isinstance(merged, MergedContext)
        assert len(merged.critical_findings) == 1
        assert len(merged.source_attributions) >= 1

    def test_example_selector(self):
        selector = ExampleSelector()
        examples = selector.select_examples(["sql_injection"], framework="fastapi", max_examples=2)
        assert len(examples) >= 1
        assert isinstance(examples[0], ExampleItem)
        assert "sql_injection" in examples[0].category.lower() or "security" in examples[0].category.lower()


class TestTemplatesAndPromptBuilder:
    """Test TemplateEngine and PromptBuilder master orchestrator."""

    def test_template_engine_rendering(self):
        engine = TemplateEngine()
        template = engine.get_template("security_review")
        assert isinstance(template, PromptTemplate)

        context_blocks = {
            "Repository Context": "Language: Python, Framework: FastAPI",
            "Critical Findings": "SQL Injection found at line 42",
            "Retrieved Knowledge": "OWASP A03 SQL Injection defense guidance",
        }
        sys_prompt, user_prompt = engine.render_template(template, context_blocks, output_format="json")
        assert "Security Review" in sys_prompt or "security" in sys_prompt.lower()
        assert "SQL Injection found at line 42" in user_prompt
        assert "JSON" in user_prompt or "json" in sys_prompt.lower()

    def test_prompt_builder_end_to_end(self):
        builder = PromptBuilder()

        findings = [
            {"title": "SQL Injection", "severity": "CRITICAL", "category": "security", "file": "app/db.py", "line": 42},
        ]
        sr = DetailedSearchResult(
            chunk_id="c1",
            document_id="OWASP-A03",
            title="OWASP SQL Injection Guidance",
            content="Always use parameterized SQL queries.",
            source_path="/kb/owasp_a03.md",
            similarity_score=0.92,
            raw_metadata={"category": "security"},
        )
        assembled = AssembledContext(
            formatted_prompt_context="### OWASP SQL Injection Guidance\nAlways use parameterized SQL queries.",
            retrieved_results=[sr],
            total_documents=1,
            sources=["/kb/owasp_a03.md"],
        )
        repo_ctx = {
            "primary_language": "python",
            "framework": "fastapi",
            "database": "postgresql",
        }

        final_prompt = builder.build_prompt(
            analysis_findings=findings,
            retrieved_context=assembled,
            repo_context=repo_ctx,
            template_name="security_review",
            output_format="json",
            max_tokens=16000,
        )

        assert isinstance(final_prompt, FinalPrompt)
        assert len(final_prompt.system_instruction) > 0
        assert len(final_prompt.user_prompt) > 0
        assert final_prompt.estimated_tokens > 0
        assert final_prompt.validation_result.is_valid
        assert "/kb/owasp_a03.md" in final_prompt.sources
