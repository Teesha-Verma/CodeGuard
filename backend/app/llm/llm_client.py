from typing import Dict, Any, Optional
import json
import time
from openai import OpenAI, AsyncOpenAI, APIError, APITimeoutError
from app.core.config import get_settings
from app.core.logger import PipelineLogger

class LLMClient:
    """Provider-agnostic LLM client for generating structured review insights."""
    
    def __init__(self, review_id: str):
        self.settings = get_settings()
        self.logger = PipelineLogger(review_id=review_id, stage="llm_client")
        self.provider = self.settings.LLM_PROVIDER
        
        # Determine API Key and Model based on provider
        if self.provider == "groq":
            self.api_key = self.settings.GROQ_API_KEY or self.settings.LLM_API_KEY
            self.model = self.settings.GROQ_MODEL or self.settings.LLM_MODEL
            self.base_url = "https://api.groq.com/openai/v1"
            if not self.api_key:
                self.logger.warning("No GROQ_API_KEY or LLM_API_KEY found, Groq reasoning will fail.")
        elif self.provider == "openai":
            self.api_key = self.settings.LLM_API_KEY
            self.model = self.settings.LLM_MODEL
            self.base_url = None  # Standard OpenAI endpoint
            if not self.api_key:
                self.logger.warning("No LLM_API_KEY found, OpenAI reasoning will fail.")
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
            
        # Instantiate both sync and async clients for maximum adaptability
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.async_client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate_structured(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Generates a structured JSON response from the LLM.
        Synchronous interface called by review pipeline.
        Includes robust retry-safe behavior and timeout handling.
        """
        self.logger.debug(f"Sending request to {self.provider} ({self.model})")
        
        max_retries = 3
        backoff_factor = 2
        timeout = float(self.settings.LLM_TIMEOUT)
        
        # Ensure system prompt instructs JSON response for model compliance with json_object mode
        enhanced_system_prompt = system_prompt
        if "json" not in system_prompt.lower():
            enhanced_system_prompt += "\n\nIMPORTANT: You must return a valid JSON object."
            
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=self.settings.LLM_TEMPERATURE,
                    response_format={"type": "json_object"},
                    timeout=timeout
                )
                
                content = response.choices[0].message.content
                if content:
                    self.logger.debug(f"Received successful response from {self.provider}")
                    return json.loads(content)
                
                self.logger.warning(f"Empty content returned from {self.provider}")
                return None
                
            except APITimeoutError as te:
                self.logger.warning(f"Timeout on attempt {attempt}/{max_retries}: {str(te)}")
                if attempt == max_retries:
                    self.logger.error("LLM API request timed out after maximum retries.")
                    return None
            except APIError as ae:
                # Retry on 429 Rate Limit or 5xx Server Errors, but fail immediately on 401/403/400
                is_transient = ae.status_code in [429, 500, 502, 503, 504]
                self.logger.warning(
                    f"API Error ({ae.status_code}) on attempt {attempt}/{max_retries}: {str(ae)}"
                )
                if not is_transient or attempt == max_retries:
                    self.logger.error(f"Non-transient or final API Error: {str(ae)}")
                    return None
            except json.JSONDecodeError as jde:
                self.logger.error(f"JSON Decode Error on attempt {attempt}/{max_retries}: {str(jde)}")
                # Retrying JSON generation might help if the model was slightly off
                if attempt == max_retries:
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error on attempt {attempt}/{max_retries}: {str(e)}")
                if attempt == max_retries:
                    return None
                    
            # Apply exponential backoff before retry
            sleep_time = backoff_factor ** attempt
            self.logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
            
        return None

    async def generate_structured_async(self, system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
        """
        Asynchronously generates a structured JSON response from the LLM.
        Useful for future-proofing and high-concurrency async parts of the application.
        """
        self.logger.debug(f"Sending async request to {self.provider} ({self.model})")
        
        max_retries = 3
        backoff_factor = 2
        timeout = float(self.settings.LLM_TIMEOUT)
        
        # Ensure system prompt instructs JSON response for model compliance with json_object mode
        enhanced_system_prompt = system_prompt
        if "json" not in system_prompt.lower():
            enhanced_system_prompt += "\n\nIMPORTANT: You must return a valid JSON object."
            
        import asyncio
        for attempt in range(1, max_retries + 1):
            try:
                response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": enhanced_system_prompt},
                        {"role": "user", "content": user_content}
                    ],
                    temperature=self.settings.LLM_TEMPERATURE,
                    response_format={"type": "json_object"},
                    timeout=timeout
                )
                
                content = response.choices[0].message.content
                if content:
                    self.logger.debug(f"Received successful async response from {self.provider}")
                    return json.loads(content)
                
                self.logger.warning(f"Empty content returned from {self.provider} (async)")
                return None
                
            except APITimeoutError as te:
                self.logger.warning(f"Async timeout on attempt {attempt}/{max_retries}: {str(te)}")
                if attempt == max_retries:
                    self.logger.error("LLM Async API request timed out after maximum retries.")
                    return None
            except APIError as ae:
                is_transient = ae.status_code in [429, 500, 502, 503, 504]
                self.logger.warning(
                    f"Async API Error ({ae.status_code}) on attempt {attempt}/{max_retries}: {str(ae)}"
                )
                if not is_transient or attempt == max_retries:
                    self.logger.error(f"Non-transient or final Async API Error: {str(ae)}")
                    return None
            except json.JSONDecodeError as jde:
                self.logger.error(f"Async JSON Decode Error on attempt {attempt}/{max_retries}: {str(jde)}")
                if attempt == max_retries:
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected async error on attempt {attempt}/{max_retries}: {str(e)}")
                if attempt == max_retries:
                    return None
                    
            # Apply exponential backoff before retry
            sleep_time = backoff_factor ** attempt
            self.logger.info(f"Retrying async call in {sleep_time} seconds...")
            await asyncio.sleep(sleep_time)
            
        return None
