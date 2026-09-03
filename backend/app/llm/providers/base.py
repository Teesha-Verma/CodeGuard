"""
CodeGuard V2 — Base LLM Provider Interface.

Defines the contract for all reasoning providers (Groq, Gemini, etc.).
"""
from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.llm.models import LLMRequest, LLMResponse
from app.llm.errors import ErrorClassification, ErrorClassifier


class LLMProvider(ABC):
    """Abstract base provider for LLM reasoning and structured generation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier ('groq' | 'gemini')."""
        pass

    @property
    @abstractmethod
    def primary_model(self) -> str:
        """Configured primary model for this provider."""
        pass

    @property
    @abstractmethod
    def fallback_models(self) -> List[str]:
        """Ordered candidate fallback models within this provider."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

    @abstractmethod
    def generate(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate unstructured text response."""
        pass

    @abstractmethod
    def generate_structured(self, request: LLMRequest, tracker: Optional[Any] = None) -> LLMResponse:
        """Generate normalized structured JSON response."""
        pass

    def classify_error(self, error: Exception) -> ErrorClassification:
        """Classify an exception using the unified ErrorClassifier."""
        return ErrorClassifier.classify(error, provider=self.name)

    def clean_json_text(self, text: str) -> str:
        """Strip markdown code block fencing from model JSON text."""
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return cleaned.strip()

    def parse_json_safely(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse text as JSON, returning None on failure."""
        cleaned = self.clean_json_text(text)
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            return {"raw_output": str(parsed)}
        except Exception:
            return None
