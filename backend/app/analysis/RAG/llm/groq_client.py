"""
Groq API client implementation.
"""
import os
import json
import httpx
from typing import Any
from .base_client import BaseLLMClient
from ..responses.review_schema import ReviewResponse


class GroqClient(BaseLLMClient):
    """
    Client for Groq API using OpenAI compatible endpoints.
    """
    
    DEFAULT_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    DEFAULT_MODEL = "llama-3.3-70b-versatile"

    def __init__(self, api_key: str | None = None, model: str | None = None, api_url: str | None = None, config: Any = None):
        """
        Initialize the Groq client.
        """
        if config is not None:
            self.config = config
            self.api_key = getattr(config, "api_key", None) or os.environ.get("GROQ_API_KEY", "mock_key")
            self.model = getattr(config, "model", None) or self.DEFAULT_MODEL
        else:
            self.api_key = api_key or os.environ.get("GROQ_API_KEY", "mock_key")
            self.model = model or self.DEFAULT_MODEL
            from ..config.llm_config import LLMConfig
            self.config = LLMConfig(api_key=self.api_key, model=self.model)

        self.api_url = api_url or self.DEFAULT_API_URL
        self._client = httpx.Client(
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=120.0
        )

    @property
    def provider_name(self) -> str:
        return "groq"

    def generate_review(self, prompt: Any, config: Any = None) -> ReviewResponse:
        """
        Generate a structured review response using JSON mode.
        """
        model = config.get("model", self.model) if config else self.model
        
        # Ensure prompt is correctly formatted
        messages = prompt if isinstance(prompt, list) else [{"role": "user", "content": str(prompt)}]
        
        payload = {
            "model": model,
            "messages": messages,
            "response_format": {"type": "json_object"}
        }

        response = self._client.post(self.api_url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Parse content as JSON and validate with Pydantic
        parsed_json = json.loads(content)
        return ReviewResponse.model_validate(parsed_json)

    def generate_raw(self, prompt_text: str, system_instruction: str = "") -> str:
        """
        Generate raw text response.
        """
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt_text})
        
        payload = {
            "model": self.model,
            "messages": messages
        }

        response = self._client.post(self.api_url, json=payload)
        response.raise_for_status()
        
        data = response.json()
        return data["choices"][0]["message"]["content"]
