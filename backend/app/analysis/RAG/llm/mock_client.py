"""
Mock client for offline testing.
"""
from typing import Any
from .base_client import BaseLLMClient
from ..responses.review_schema import ReviewResponse, ReviewFinding


class MockGroqClient(BaseLLMClient):
    """
    A mock LLM client that returns deterministic responses.
    """

    @property
    def provider_name(self) -> str:
        return "mock_groq"

    def generate_review(self, prompt: Any, config: Any = None) -> ReviewResponse:
        """
        Return a mock ReviewResponse.
        """
        finding = ReviewFinding(
            title="Mock Vulnerability",
            severity="high",
            file_path="mock_file.py",
            line_number=42,
            evidence="eval(user_input)",
            reasoning="Using eval on user input can lead to arbitrary code execution.",
            priority="high",
            remediation="Use literal_eval instead of eval.",
            code_suggestion="ast.literal_eval(user_input)",
            references=["CWE-94"]
        )

        return ReviewResponse(
            review_summary="Mock review summary.",
            overall_severity="high",
            findings=[finding],
            evidence_summary="Found eval statement.",
            reasoning_trace="Evaluated code for security risks.",
            confidence=0.99,
            priority="high",
            remediation_summary="Fix the eval statement.",
            code_suggestions=["Use ast.literal_eval"],
            references=["https://cwe.mitre.org/data/definitions/94.html"],
            review_metadata={"mock": True}
        )

    def generate_raw(self, prompt_text: str, system_instruction: str = "") -> str:
        """
        Return a mock raw text response.
        """
        return "This is a mock raw response."
