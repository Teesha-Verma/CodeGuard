from typing import Dict, Any, Optional
from google import genai
from google.genai import types
import json
from app.core.config import get_settings
from app.core.logger import PipelineLogger

class LLMClient:
    """Provider-agnostic LLM client for generating structured review insights."""
    
    def __init__(self, review_id: str):
        self.settings = get_settings()
        self.logger = PipelineLogger(review_id=review_id, stage="llm_client")
        self.provider = self.settings.LLM_PROVIDER
        
        if self.provider == "gemini":
            if not self.settings.LLM_API_KEY:
                self.logger.warning("No LLM_API_KEY found, LLM reasoning will fail.")
            self.client = genai.Client(api_key=self.settings.LLM_API_KEY)
        elif self.provider == "openai":
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.settings.LLM_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def generate_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """Generates a structured JSON response from the LLM."""
        
        self.logger.debug(f"Sending request to {self.provider} ({self.settings.LLM_MODEL})")
        
        try:
            if self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.settings.LLM_MODEL,
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=self.settings.LLM_TEMPERATURE,
                        response_mime_type="application/json",
                    ),
                )
                if response.text:
                    return json.loads(response.text)
                return None
                
            elif self.provider == "openai":
                # Synchronous wrapper for V1, would be async in real world
                import asyncio
                loop = asyncio.get_event_loop()
                response = loop.run_until_complete(
                    self.client.chat.completions.create(
                        model=self.settings.LLM_MODEL,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_content}
                        ],
                        temperature=self.settings.LLM_TEMPERATURE,
                        response_format={"type": "json_object"}
                    )
                )
                if response.choices[0].message.content:
                    return json.loads(response.choices[0].message.content)
                return None
                
        except Exception as e:
            self.logger.error(f"LLM API Error: {str(e)}")
            return None
