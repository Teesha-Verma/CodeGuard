"""
Knowledge & RAG Layer for CodeGuard V2.
"""

from typing import TYPE_CHECKING

__all__ = [
    "KnowledgeDocument",
    "KnowledgeChunk",
    "RepositoryContext",
    "RetrievalRequest",
    "RetrievalResult",
    "RetrievedContext",
    "KnowledgeQueryEngine",
    "SemanticRetriever",
]

def __getattr__(name: str):
    if name in (
        "KnowledgeDocument",
        "KnowledgeChunk",
        "RepositoryContext",
        "RetrievalRequest",
        "RetrievalResult",
        "RetrievedContext",
    ):
        import app.analysis.knowledge.models as models
        return getattr(models, name)
    
    if name == "KnowledgeQueryEngine":
        import app.analysis.knowledge.query_engine as query_engine
        return getattr(query_engine, name)
        
    if name == "SemanticRetriever":
        import app.analysis.knowledge.retrievers as retrievers
        return getattr(retrievers, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
