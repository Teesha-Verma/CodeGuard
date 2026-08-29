"""
Legacy Groq client module, migrated to GeminiClient for backward compatibility.
"""
import warnings
from .gemini_client import GeminiClient

warnings.warn(
    "GroqClient is deprecated and will be removed. Use GeminiClient instead.",
    DeprecationWarning,
    stacklevel=2,
)

GroqClient = GeminiClient
