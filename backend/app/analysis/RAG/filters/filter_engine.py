from typing import List, Dict, Any
from app.analysis.RAG.search.result import DetailedSearchResult

class MetadataFilterEngine:
    """
    Engine to apply pre-filters on metadata and post-filters on search results.
    """

    def apply_pre_filters(self, query_filters: Dict[str, Any], candidate_metadatas: List[Dict[str, Any]]) -> List[bool]:
        """
        Applies filters to candidate metadata dictionaries, returning a boolean mask.
        Supports filtering by category, language, framework, database, severity, etc.
        """
        mask = []
        for metadata in candidate_metadatas:
            match = True
            for key, expected_values in query_filters.items():
                if key not in metadata:
                    match = False
                    break
                
                actual_value = metadata[key]
                if isinstance(expected_values, list):
                    if isinstance(actual_value, list):
                        if not any(val in actual_value for val in expected_values):
                            match = False
                            break
                    else:
                        if actual_value not in expected_values:
                            match = False
                            break
                else:
                    if actual_value != expected_values:
                        match = False
                        break
            mask.append(match)
        return mask

    def apply_post_filters(self, results: List[DetailedSearchResult], filter_criteria: Dict[str, Any]) -> List[DetailedSearchResult]:
        """
        Applies post-retrieval filters on DetailedSearchResult objects.
        """
        filtered_results = []
        for result in results:
            match = True
            for key, expected_values in filter_criteria.items():
                actual_value = result.raw_metadata.get(key)
                if actual_value is None:
                    # check if the attribute exists on DetailedSearchResult
                    if hasattr(result, key):
                        actual_value = getattr(result, key)
                    else:
                        match = False
                        break
                
                if isinstance(expected_values, list):
                    if isinstance(actual_value, list):
                        if not any(val in actual_value for val in expected_values):
                            match = False
                            break
                    else:
                        if actual_value not in expected_values:
                            match = False
                            break
                else:
                    if actual_value != expected_values:
                        match = False
                        break
            if match:
                filtered_results.append(result)
                
        return filtered_results
