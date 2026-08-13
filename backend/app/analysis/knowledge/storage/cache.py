import logging
import time
from collections import OrderedDict
from typing import Any, Hashable

from app.analysis.knowledge.constants import DEFAULT_CACHE_MAX_SIZE, DEFAULT_CACHE_TTL_SECONDS

logger = logging.getLogger(__name__)

class KnowledgeCache:
    """
    Lightweight in-memory LRU cache with TTL support.
    
    Used for caching:
    - Loaded documents
    - Generated embeddings  
    - Retrieval results
    
    The cache is optional and can be disabled.
    """
    
    def __init__(self, max_size: int = DEFAULT_CACHE_MAX_SIZE, ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS, enabled: bool = True):
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._enabled = enabled
        self._store: OrderedDict[str, tuple[Any, float]] = OrderedDict()  # key -> (value, timestamp)
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Any | None:
        if not self._enabled:
            return None
            
        if key not in self._store:
            self._misses += 1
            return None
            
        value, timestamp = self._store[key]
        if time.time() - timestamp > self._ttl:
            # Expired
            del self._store[key]
            self._misses += 1
            return None
            
        # Update LRU order
        self._store.move_to_end(key)
        self._hits += 1
        return value
    
    def put(self, key: str, value: Any) -> None:
        if not self._enabled:
            return
            
        if key in self._store:
            del self._store[key]
        elif len(self._store) >= self._max_size:
            # Evict first (oldest) item
            self._store.popitem(last=False)
            
        self._store[key] = (value, time.time())
    
    def invalidate(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    def clear(self) -> None:
        self._store.clear()
        self._hits = 0
        self._misses = 0
    
    @property
    def stats(self) -> dict[str, Any]:
        total = self._hits + self._misses
        hit_rate = (self._hits / total) if total > 0 else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "size": len(self._store),
            "max_size": self._max_size,
            "enabled": self._enabled
        }
    
    def _evict_expired(self) -> int:
        current_time = time.time()
        expired_keys = [k for k, v in self._store.items() if current_time - v[1] > self._ttl]
        for k in expired_keys:
            del self._store[k]
        return len(expired_keys)
