from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.analysis.RAG.context.base import RetrievalContextSignal

class RetrievalQuery(BaseModel):
    """
    Constructed retrieval query and associated metadata filters.
    """
    raw_query_string: str
    boosted_keywords: List[str] = Field(default_factory=list)
    filters: Dict[str, Any] = Field(default_factory=dict)
    source_signal_types: List[str] = Field(default_factory=list)


class QueryBuilder:
    """
    Builds semantic search queries from multiple retrieval context signals.
    """

    def build_query(
        self, signals: List[RetrievalContextSignal], default_category: str = "security"
    ) -> RetrievalQuery:
        """
        Constructs an optimized semantic query text combining framework, language,
        vulnerability type, and key terms.
        Combines candidate metadata filters from all input context signals.
        """
        query_terms: List[str] = []
        boosted_keywords: List[str] = []
        filters: Dict[str, Any] = {}
        signal_types: List[str] = []

        all_languages: List[str] = []
        all_frameworks: List[str] = []
        all_databases: List[str] = []
        all_tags: List[str] = []

        for signal in signals:
            signal_types.append(signal.signal_type)

            # Extract terms
            if hasattr(signal, "query_tokens") and signal.query_tokens:
                query_terms.extend(signal.query_tokens)
            if hasattr(signal, "vulnerability_types") and signal.vulnerability_types:
                query_terms.extend(signal.vulnerability_types)
                boosted_keywords.extend(signal.vulnerability_types)

            if hasattr(signal, "languages") and signal.languages:
                all_languages.extend(signal.languages)
                query_terms.extend(signal.languages)
            if hasattr(signal, "frameworks") and signal.frameworks:
                all_frameworks.extend(signal.frameworks)
                query_terms.extend(signal.frameworks)
            if hasattr(signal, "databases") and signal.databases:
                all_databases.extend(signal.databases)
                query_terms.extend(signal.databases)
            if hasattr(signal, "orms") and signal.orms:
                query_terms.extend(signal.orms)
            if hasattr(signal, "tags") and signal.tags:
                all_tags.extend(signal.tags)

        if default_category:
            filters["category"] = default_category
        if all_languages:
            filters["languages"] = list(dict.fromkeys(all_languages))
        if all_frameworks:
            filters["frameworks"] = list(dict.fromkeys(all_frameworks))
        if all_databases:
            filters["databases"] = list(dict.fromkeys(all_databases))
        if all_tags:
            filters["tags"] = list(dict.fromkeys(all_tags))

        raw_query_string = " ".join(dict.fromkeys(query_terms)).strip()
        if not raw_query_string:
            raw_query_string = default_category

        return RetrievalQuery(
            raw_query_string=raw_query_string,
            boosted_keywords=list(dict.fromkeys(boosted_keywords)),
            filters=filters,
            source_signal_types=list(dict.fromkeys(signal_types)),
        )
