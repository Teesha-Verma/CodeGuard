"""
CodeGuard V2 — Real RAG Knowledge Retrieval Integration Tests.

Validates:
- Real RAG knowledge retrieval using Gemini Embedding 2
- Heuristic and semantic reranking
- Context assembly for prompt grounding
- Injection of real RAG knowledge into code review reasoning
"""

import pytest
from app.core.config import get_settings
from app.analysis.RAG.knowledge_retrieval_service import KnowledgeRetrievalService
from app.reasoning.review_generator import ReviewGenerator


@pytest.fixture(scope="module")
def settings():
    conf = get_settings()
    if not conf.GEMINI_API_KEY or conf.GEMINI_API_KEY in ("your_gemini_api_key_here", "mock_key"):
        pytest.skip("Real GEMINI_API_KEY not configured; skipping real RAG tests.")
    return conf


class TestRAGRealIntegration:
    """Real RAG knowledge retrieval and prompt grounding tests."""

    def test_rag_real_knowledge_retrieval(self, settings):
        """Verify KnowledgeRetrievalService retrieves relevant knowledge using real embeddings."""
        kb_service = KnowledgeRetrievalService.get_instance()
        assert kb_service.embedding_provider.dimension == 768

        finding = {
            "line": 12,
            "issue": "SQL injection vulnerability: unsanitized user parameter in cursor.execute",
            "severity": "critical",
            "sources": ["ast", "bandit", "dataflow"],
            "evidence": {
                "ast_nodes": [{"pattern": "eval_detection", "message": "SQL formatting"}],
                "linter_rules": [{"tool": "bandit", "rule_id": "B608", "message": "Possible SQL injection"}],
                "dataflow_findings": [{"rule_id": "SQL_INJECTION", "sink_node": "cursor.execute"}],
            }
        }

        # Ensure vector store contains real embedded knowledge
        if kb_service.vector_store.count() == 0:
            from app.analysis.RAG.models.documents import EmbeddingDocument
            doc_text = "Security Standard: SQL Injection (CWE-89, OWASP-A03). Always use parameterized queries or prepared statements to prevent SQL injection."
            doc_emb = kb_service.embedding_provider.embed_text(doc_text)
            kb_service.vector_store.add_documents([
                EmbeddingDocument(
                    chunk_id="rule_cwe_89",
                    document_id="doc_sql_inj",
                    content=doc_text,
                    embedding=doc_emb,
                    metadata={
                        "category": "security",
                        "tags": ["sql_injection", "cwe-89", "critical"],
                        "languages": ["python"],
                        "frameworks": ["fastapi"],
                        "databases": ["postgresql"],
                    }
                )
            ])

        repo_context = {
            "framework": "fastapi",
            "database": "postgresql",
        }
        assembled = kb_service.retrieve_for_finding(finding=finding, repo_context=repo_context, top_k=2)
        assert assembled is not None
        assert assembled.formatted_prompt_context is not None

        # Verify retrieved context contains meaningful security or SQL guidance
        context_text = assembled.formatted_prompt_context.lower()
        assert any(term in context_text for term in ["sql", "injection", "parameter", "query", "cwe-89", "security"])

    def test_rag_real_review_generator_grounded_execution(self, settings):
        """Verify ReviewGenerator uses real RAG grounding and Gemini reasoning."""
        generator = ReviewGenerator(review_id="test_rag_grounded_gen")

        aggregated_data = {
            "file_path": "app/auth/user_login.py",
            "changed_lines": [5, 10],
            "code_context": [
                {
                    "start_line": 1,
                    "code": "import sqlite3\n\ndef login(username, password):\n    conn = sqlite3.connect('app.db')\n    query = f'SELECT * FROM users WHERE user={username} AND pass={password}'\n    return conn.execute(query).fetchone()\n"
                }
            ],
            "mutation_analysis": [],
            "scope_analysis": [],
            "linter_findings": [
                {
                    "line": 5,
                    "tool": "bandit",
                    "rule": "B608",
                    "message": "Possible SQL injection vector through string-based query construction",
                    "severity": "critical"
                }
            ],
            "heuristic_findings": [],
            "dataflow_analysis": [
                {
                    "sink_line": 5,
                    "rule_id": "SQL_INJECTION",
                    "title": "SQL Injection",
                    "description": "User input directly flows into SQL query execution without parameterization.",
                    "severity": "critical"
                }
            ],
            "repository_intelligence": {
                "framework": "fastapi",
                "database": "postgresql"
            }
        }

        issues = generator.generate(aggregated_data)
        assert len(issues) >= 1

        top_issue = issues[0]
        assert top_issue.line == 5
        assert top_issue.severity.lower() in ("critical", "high")
        assert top_issue.confidence >= 0.7
        assert top_issue.reasoning_source == "llm"
        assert top_issue.root_cause != ""
        assert top_issue.fix != ""
        assert len(top_issue.reasoning_trace) > 0
