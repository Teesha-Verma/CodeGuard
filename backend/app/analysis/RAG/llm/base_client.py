"""
Base LLM Client interface.
"""
from abc import ABC, abstractmethod
from typing import Any
from ..responses.review_schema import ReviewResponse


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_review(self, prompt: Any, config: Any = None) -> ReviewResponse:
        """
        Generate a structured review response.

        Args:
            prompt: The prompt input for the model.
            config: Optional configuration overrides.

        Returns:
            ReviewResponse: The structured review object.
        """
        pass

    @abstractmethod
    def generate_raw(self, prompt_text: str, system_instruction: str = "") -> str:
        """
        Generate raw text response.

        Args:
            prompt_text: The user prompt.
            system_instruction: Optional system instructions.

        Returns:
            str: Raw text response from the model.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Get the provider name.

        Returns:
            str: The name of the LLM provider.
        """
        pass
