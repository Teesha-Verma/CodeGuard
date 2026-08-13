"""
Context merging module.
"""
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class MergedContext(BaseModel):
    """
    Data model representing merged context from various sources.
    """
    critical_findings: List[Dict[str, Any]] = Field(default_factory=list)
    security_findings: List[Dict[str, Any]] = Field(default_factory=list)
    other_findings: List[Dict[str, Any]] = Field(default_factory=list)
    official_knowledge: List[Any] = Field(default_factory=list)
    framework_knowledge: List[Any] = Field(default_factory=list)
    general_knowledge: List[Any] = Field(default_factory=list)
    repo_rules: List[str] = Field(default_factory=list)
    architecture_context: str = ""
    source_attributions: List[str] = Field(default_factory=list)


class ContextMerger:
    """
    Merges context from analysis findings, retrieved knowledge, and repository context.
    Eliminates duplicates.
    """

    def merge_all(
        self,
        analysis_findings: List[Dict[str, Any]],
        retrieved_context: Any,
        repo_context: Optional[Dict[str, Any]] = None
    ) -> MergedContext:
        """
        Merges various context sources into a unified MergedContext object.

        Args:
            analysis_findings: List of analysis findings.
            retrieved_context: Retrieved knowledge items.
            repo_context: Repository-specific context.

        Returns:
            MergedContext containing deduplicated and categorized context.
        """
        merged = MergedContext()
        seen_findings: Set[str] = set()
        seen_knowledge: Set[str] = set()
        
        repo_context = repo_context or {}

        # Merge findings
        for finding in analysis_findings:
            finding_id = finding.get("id") or str(finding.get("description", ""))
            if finding_id in seen_findings:
                continue
            seen_findings.add(finding_id)
            
            severity = str(finding.get("severity", "")).lower()
            if severity == "critical":
                merged.critical_findings.append(finding)
            elif severity in ("high", "medium", "low"):
                merged.security_findings.append(finding)
            else:
                merged.other_findings.append(finding)

        # Merge retrieved context
        results_list = []
        if hasattr(retrieved_context, "retrieved_results"):
            results_list = retrieved_context.retrieved_results
            if hasattr(retrieved_context, "sources") and retrieved_context.sources:
                for s in retrieved_context.sources:
                    if s and s not in merged.source_attributions:
                        merged.source_attributions.append(s)
        elif isinstance(retrieved_context, list):
            results_list = retrieved_context

        for item in results_list:
            item_str = str(item)
            if item_str in seen_knowledge:
                continue
            seen_knowledge.add(item_str)
            
            source_path = getattr(item, "source_path", "")
            if not source_path and isinstance(item, dict):
                source_path = item.get("source_path", item.get("source", ""))
            if source_path and source_path not in merged.source_attributions:
                merged.source_attributions.append(source_path)

            category = getattr(item, "category", "")
            if not category and isinstance(item, dict):
                category = item.get("category", "")
            
            source_lower = str(source_path).lower()
            category_lower = str(category).lower()

            if any(std in source_lower for std in ("owasp", "cwe", "cert")):
                merged.official_knowledge.append(item)
            elif "framework" in category_lower:
                merged.framework_knowledge.append(item)
            else:
                merged.general_knowledge.append(item)

        # Merge repo context
        if repo_context:
            merged.repo_rules = repo_context.get("rules", [])
            merged.architecture_context = repo_context.get("architecture", "")

        return merged
