from pydantic import BaseModel, Field
from typing import List, Dict, Any

class DetailedSearchResult(BaseModel):
    """
    Detailed search result containing scores, metadata, and matched entities.
    """
    chunk_id: str
    document_id: str
    title: str
    content: str
    source_path: str
    similarity_score: float = 0.0
    metadata_score: float = 0.0
    rerank_score: float = 0.0
    final_score: float = 0.0
    matched_concepts: List[str] = Field(default_factory=list)
    matched_frameworks: List[str] = Field(default_factory=list)
    matched_languages: List[str] = Field(default_factory=list)
    matched_tags: List[str] = Field(default_factory=list)
    retrieval_reason: str = ""
    confidence: float = 0.0
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
