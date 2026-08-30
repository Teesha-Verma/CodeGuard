import os
from pydantic import BaseModel, Field


class LLMConfig(BaseModel):
    """Configuration for the Groq LLM API."""
    api_key: str = Field(default="", description="The Groq API key")
    model: str = Field(default="llama-3.3-70b-versatile", description="The Groq model to use")
    max_tokens: int = Field(default=4096, description="Maximum number of tokens to generate")
    timeout: float = Field(default=60.0, description="API timeout in seconds")
    max_retries: int = Field(default=2, description="Maximum number of retries for API calls")
    retry_delay: float = Field(default=1.0, description="Base delay between retries in seconds")
    json_mode: bool = Field(default=True, description="Whether to enforce JSON output")
    caching_enabled: bool = Field(default=True, description="Whether to enable response caching")

    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create a configuration instance from environment variables."""
        return cls(
            api_key=os.environ.get("GROQ_API_KEY", os.environ.get("LLM_API_KEY", "")),
            model=os.environ.get("GROQ_LLM_MODEL", os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")),
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", 4096)),
            timeout=float(os.environ.get("GROQ_TIMEOUT", os.environ.get("LLM_TIMEOUT", 60.0))),
            max_retries=int(os.environ.get("GROQ_MAX_RETRIES", os.environ.get("LLM_MAX_RETRIES", 2))),
            retry_delay=float(os.environ.get("LLM_RETRY_DELAY", 1.0)),
            json_mode=os.environ.get("LLM_JSON_MODE", "true").lower() == "true",
            caching_enabled=os.environ.get("LLM_CACHING_ENABLED", "true").lower() == "true",
        )


GroqConfig = LLMConfig
GeminiConfig = LLMConfig  # Backwards compatibility alias
