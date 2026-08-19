import time
import hashlib
import threading
from typing import Optional, Dict, Any
from collections import OrderedDict

class CacheEntry:
    """Stores cache data with its creation time for TTL expiration."""
    def __init__(self, value: str, ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() > self.expires_at

class LLMResponseCache:
    """In-memory LRU cache for storing Gemini LLM responses."""

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600, default_ttl_seconds: int = 3600):
        """
        Initialize the cache.
        """
        self.max_size = max_size
        self.default_ttl_seconds = ttl_seconds or default_ttl_seconds
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.Lock()
        
        # Stats
        self.hits = 0
        self.misses = 0

    @property
    def stats(self) -> Dict[str, Any]:
        return self.get_stats()

    def _generate_key(self, prompt_text: str, model_name: str) -> str:
        """
        Generates a SHA-256 hash key for the cache based on prompt and model.
        
        Args:
            prompt_text (str): The prompt provided to the LLM.
            model_name (str): The model used for generation.
            
        Returns:
            str: The SHA-256 hash string.
        """
        key_str = f"{prompt_text}::{model_name}"
        return hashlib.sha256(key_str.encode('utf-8')).hexdigest()

    def get(self, prompt_text: str, model_name: str) -> Optional[str]:
        """
        Retrieve a response from the cache if it exists and is valid.
        
        Args:
            prompt_text (str): The prompt text.
            model_name (str): The model name.
            
        Returns:
            Optional[str]: The cached response, or None if not found or expired.
        """
        key = self._generate_key(prompt_text, model_name)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                if not entry.is_expired():
                    # Move to end to show it was recently used (LRU logic)
                    self.cache.move_to_end(key)
                    self.hits += 1
                    return entry.value
                else:
                    # Remove expired entry
                    del self.cache[key]
                    
            self.misses += 1
            return None

    def set(self, prompt_text: str, model_name: str, response: str, ttl_seconds: Optional[int] = None) -> None:
        """
        Store a response in the cache with an optional TTL.
        
        Args:
            prompt_text (str): The prompt text.
            model_name (str): The model name.
            response (str): The LLM response string to cache.
            ttl_seconds (Optional[int]): Custom TTL for this entry.
        """
        key = self._generate_key(prompt_text, model_name)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl_seconds
        
        with self.lock:
            if key in self.cache:
                del self.cache[key]
            elif len(self.cache) >= self.max_size:
                # Remove oldest entry (FIFO in LRU context)
                self.cache.popitem(last=False)
                
            self.cache[key] = CacheEntry(value=response, ttl_seconds=ttl)

    def put(self, prompt_text: str, model_name: str, response: Any, ttl_seconds: Optional[int] = None) -> None:
        """Alias for set."""
        self.set(prompt_text, model_name, response, ttl_seconds)

    def invalidate(self, prompt_text: str, model_name: str) -> None:
        """
        Invalidate a specific cache entry.
        
        Args:
            prompt_text (str): The prompt text.
            model_name (str): The model name.
        """
        key = self._generate_key(prompt_text, model_name)
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                
    def clear(self) -> None:
        """Clear the entire cache and reset stats."""
        with self.lock:
            self.cache.clear()
            self.hits = 0
            self.misses = 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Return cache statistics including hits, misses, and hit ratio.
        
        Returns:
            Dict[str, Any]: Cache statistics dictionary.
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_ratio = (self.hits / total_requests) if total_requests > 0 else 0.0
            
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": hit_ratio,
            }
