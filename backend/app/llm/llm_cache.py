"""
CodeGuard V2 — In-Memory LLM Response Cache & Prompt Deduplication.

Prevents duplicate generation requests for identical findings/prompts across
review workflows using deterministic SHA-256 keys and thread-safe LRU caching.
"""
from __future__ import annotations

import time
import hashlib
import threading
from collections import OrderedDict
from typing import Any, Dict, Optional

from app.core.config import get_settings


class CacheEntry:
    """Stores structured LLM response with TTL expiration."""

    def __init__(self, value: Dict[str, Any], ttl_seconds: int):
        self.value = value
        self.expires_at = time.time() + ttl_seconds

    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class LLMStructuredCache:
    """Thread-safe LRU cache for structured LLM responses."""

    def __init__(self, max_size: int = 500, default_ttl_seconds: int = 3600):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    @staticmethod
    def generate_key(system_prompt: str, user_content: str, model: str) -> str:
        """Generate a stable, deterministic SHA-256 key from prompt content and model."""
        key_raw = f"{model.strip()}::{system_prompt.strip()}::{user_content.strip()}"
        return hashlib.sha256(key_raw.encode("utf-8")).hexdigest()

    def get(self, system_prompt: str, user_content: str, model: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached structured response if available and unexpired."""
        settings = get_settings()
        if not settings.LLM_CACHE_ENABLED:
            return None

        key = self.generate_key(system_prompt, user_content, model)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    self._cache.move_to_end(key)
                    self.hits += 1
                    # Return a shallow copy of the dict to prevent mutation of cached data
                    return dict(entry.value)
                else:
                    del self._cache[key]
            self.misses += 1
            return None

    def set(
        self,
        system_prompt: str,
        user_content: str,
        model: str,
        response: Dict[str, Any],
        ttl_seconds: Optional[int] = None,
    ) -> None:
        """Store structured response in cache."""
        settings = get_settings()
        if not settings.LLM_CACHE_ENABLED or not isinstance(response, dict):
            return

        key = self.generate_key(system_prompt, user_content, model)
        ttl = ttl_seconds if ttl_seconds is not None else settings.LLM_CACHE_TTL or self.default_ttl_seconds

        with self._lock:
            if key in self._cache:
                del self._cache[key]
            elif len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
            self._cache[key] = CacheEntry(value=dict(response), ttl_seconds=ttl)

    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._cache.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> Dict[str, Any]:
        """Return cache hit/miss statistics."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": (self.hits / (self.hits + self.misses)) if (self.hits + self.misses) > 0 else 0.0,
            }


_global_cache = LLMStructuredCache()


def get_llm_cache() -> LLMStructuredCache:
    """Return the global LLM structured cache singleton."""
    return _global_cache
