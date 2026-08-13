import os
from pydantic import BaseModel, Field

class LLMConfig(BaseModel):
    """Configuration for the Groq LLM API."""
    api_key: str = Field(default="", description="The Groq API key")
    model: str = Field(default="llama-3.3-70b-versatile", description="The Groq model to use")
    temperature: float = Field(default=0.2, description="Sampling temperature")
    top_p: float = Field(default=0.95, description="Nucleus sampling parameter")
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
            api_key=os.environ.get("GROQ_API_KEY", ""),
            model=os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
            temperature=float(os.environ.get("GROQ_TEMPERATURE", 0.2)),
            top_p=float(os.environ.get("GROQ_TOP_P", 0.95)),
            max_tokens=int(os.environ.get("GROQ_MAX_TOKENS", 4096)),
            timeout=float(os.environ.get("GROQ_TIMEOUT", 60.0)),
            max_retries=int(os.environ.get("GROQ_MAX_RETRIES", 3)),
            retry_delay=float(os.environ.get("GROQ_RETRY_DELAY", 1.0)),
            json_mode=os.environ.get("GROQ_JSON_MODE", "true").lower() == "true",
            caching_enabled=os.environ.get("GROQ_CACHING_ENABLED", "true").lower() == "true"
        )


GroqConfig = LLMConfig
