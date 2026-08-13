"""
Retrieval Cache implementation for CodeGuard V2 RAG Phase 2.
"""

import time
import hashlib
import json
from collections import OrderedDict
from typing import Dict, Any, Optional, Union, List

from app.analysis.RAG.query_builder.builder import RetrievalQuery
from app.analysis.RAG.search.result import DetailedSearchResult
# Assuming AssembledContext is imported from context.assembler
from app.analysis.RAG.context.assembler import AssembledContext


class RetrievalCache:
    """
    In-memory LRU cache for mapping RetrievalQuery to AssembledContext 
    or List[DetailedSearchResult]. Supports TTL (time-to-live) and stats tracking.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        """
        Initialize the RetrievalCache.
        
        Args:
            max_size: Maximum number of entries to keep in the cache.
            ttl_seconds: Time to live for each cache entry in seconds.
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        
        # Using OrderedDict to maintain insertion order for LRU logic
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        
        # Stats tracking
        self._hits = 0
        self._misses = 0

    def _generate_key(self, query: Union[str, RetrievalQuery]) -> str:
        """
        Generates a unique deterministic string key for a RetrievalQuery or string key.
        """
        if isinstance(query, str):
            return hashlib.sha256(query.encode('utf-8')).hexdigest()
        
        query_text = getattr(query, "raw_query_string", getattr(query, "text", str(query)))
        metadata_reqs = getattr(query, "filters", getattr(query, "metadata_requirements", {}))
        
        raw_key = f"{query_text}|{json.dumps(metadata_reqs, sort_keys=True)}"
        return hashlib.sha256(raw_key.encode('utf-8')).hexdigest()

    def get(self, query: Union[str, RetrievalQuery]) -> Optional[Union[AssembledContext, List[DetailedSearchResult]]]:
        """
        Retrieve a cached response for a given query, if it exists and is not expired.
        """
        key = self._generate_key(query)
        
        if key in self._cache:
            entry = self._cache[key]
            
            # Check TTL
            if time.time() - entry["timestamp"] > self.ttl_seconds:
                # Expired
                del self._cache[key]
                self._misses += 1
                return None
                
            # Hit! Move to end to mark as recently used (LRU)
            self._cache.move_to_end(key)
            self._hits += 1
            return entry["data"]
            
        self._misses += 1
        return None

    def put(self, query: Union[str, RetrievalQuery], data: Union[AssembledContext, List[DetailedSearchResult]]) -> None:
        """
        Cache a response for a given query.
        """
        if self.max_size <= 0:
            return
            
        key = self._generate_key(query)
        
        # If exists, update and mark as recently used
        if key in self._cache:
            self._cache.move_to_end(key)
        else:
            # If full, remove the least recently used item (the first in the OrderedDict)
            if len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)
                
        self._cache[key] = {
            "data": data,
            "timestamp": time.time()
        }

    @property
    def stats(self) -> Dict[str, Any]:
        """Property alias for get_stats()."""
        return self.get_stats()

    def get_stats(self) -> Dict[str, Any]:
        """
        Retrieve cache performance statistics.
        """
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_ratio": self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0.0
        }
