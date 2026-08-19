import os
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for the Gemini LLM API."""
    api_key: str = Field(default="", description="The Gemini API key")
    model: str = Field(default="gemini-3.6-flash", description="The Gemini model to use")
    max_tokens: int = Field(default=4096, description="Maximum number of tokens to generate")
    timeout: float = Field(default=60.0, description="API timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries for API calls")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")
    json_mode: bool = Field(default=True, description="Whether to enforce JSON output")
    caching_enabled: bool = Field(default=True, description="Whether to enable response caching")

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create a configuration instance from environment variables."""
        return cls(
            api_key=os.environ.get("GEMINI_API_KEY", os.environ.get("LLM_API_KEY", "")),
            model=os.environ.get("GEMINI_LLM_MODEL", os.environ.get("LLM_MODEL", "gemini-3.6-flash")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", 4096)),
            timeout=float(os.environ.get("GEMINI_TIMEOUT", os.environ.get("LLM_TIMEOUT", 60.0))),
            max_retries=int(os.environ.get("GEMINI_MAX_RETRIES", os.environ.get("LLM_MAX_RETRIES", 3))),
            retry_delay=float(os.environ.get("LLM_RETRY_DELAY", 1.0)),
            json_mode=os.environ.get("LLM_JSON_MODE", "true").lower() == "true",
            caching_enabled=os.environ.get("LLM_CACHING_ENABLED", "true").lower() == "true",
        )


GeminiConfig = LLMConfig
GroqConfig = LLMConfig  # Backwards compatibility alias
