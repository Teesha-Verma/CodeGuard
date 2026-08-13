"""
Constants and configuration for the Knowledge & RAG Layer.
"""

from enum import Enum

# Embedding
DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004"
DEFAULT_EMBEDDING_DIMENSION = 768
MAX_EMBEDDING_BATCH_SIZE = 100
EMBEDDING_TASK_TYPE = "RETRIEVAL_DOCUMENT"
QUERY_TASK_TYPE = "RETRIEVAL_QUERY"

# Chunking
DEFAULT_CHUNK_SIZE = 512
DEFAULT_CHUNK_OVERLAP = 64
MIN_CHUNK_SIZE = 50
MAX_CHUNK_SIZE = 2048

# Retrieval
DEFAULT_TOP_K = 10
DEFAULT_SIMILARITY_THRESHOLD = 0.65
MAX_TOP_K = 50

# Document Categories
class DocumentCategory(str, Enum):
    """Enumeration of knowledge document categories."""
    SECURITY = "security"
    BEST_PRACTICE = "best_practice"
    PATTERN = "pattern"
    HISTORICAL = "historical"
    REPOSITORY = "repository"
    OWASP = "owasp"
    CWE = "cwe"

# Cache
DEFAULT_CACHE_TTL_SECONDS = 3600
DEFAULT_CACHE_MAX_SIZE = 1000

# Storage
VECTOR_INDEX_FILENAME = "knowledge_index.faiss"
METADATA_TABLE_PREFIX = "knowledge_"

# Reranker weights
DEFAULT_SIMILARITY_WEIGHT = 0.6
DEFAULT_METADATA_WEIGHT = 0.2
DEFAULT_CATEGORY_WEIGHT = 0.2
