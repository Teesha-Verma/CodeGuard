from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MergedReview(BaseModel):
    """
    Pydantic v2 model for representing a merged review containing both static analysis
    findings and LLM-generated reasoning.
    """
    summary: str = Field(..., description="Summary of the merged review")
    overall_severity: str = Field(..., description="Overall severity level of findings")
    findings: List[Dict[str, Any]] = Field(
        default_factory=list, description="List of combined findings without duplicates"
    )
    confidence_score: float = Field(
        ..., description="Calculated confidence score based on finding consensus"
    )
    priority: str = Field(..., description="Priority level for fixing issues")
    sources: List[str] = Field(
        default_factory=list, description="Sources of findings (e.g., Static, LLM)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata regarding the merge process"
    )


class ReviewMerger:
    """
    Merges static analysis findings with LLM-generated review insights.
    """

    def merge_reviews(
        self,
        static_findings: List[Dict[str, Any]],
        llm_review: Any,
        retrieved_context: Any = None
    ) -> MergedReview:
        """
        Merges static findings with LLM findings, removes duplicates, recalculates overall
        confidence score and severity level.

        Args:
            static_findings: Findings from static analysis tools.
            llm_review: Findings and reasoning from the LLM execution.
            retrieved_context: Optional context retrieved during RAG.

        Returns:
            A MergedReview instance containing deduplicated findings and recalculated metrics.
        """
        # Note: Implementation logic for deduplication and severity/confidence recalculation
        # will go here.
        
        # Placeholder for mock processing
        merged_findings = list(static_findings)
        
        if hasattr(llm_review, "findings"):
            merged_findings.extend(llm_review.findings)
        elif isinstance(llm_review, dict) and "findings" in llm_review:
            merged_findings.extend(llm_review["findings"])

        # Deduplication logic
        unique_findings = []
        seen = set()
        for f in merged_findings:
            if hasattr(f, "model_dump"):
                f_dict = f.model_dump()
            elif isinstance(f, dict):
                f_dict = f
            else:
                f_dict = {"title": str(f)}

            key = str(f_dict.get("title", "")) + str(f_dict.get("file_path", ""))
            if key not in seen:
                seen.add(key)
                unique_findings.append(f_dict)

        severity_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        max_rank = 1

        for f in unique_findings:
            sev = "info"
            if isinstance(f, dict):
                sev = str(f.get("severity", "info")).lower()
            elif hasattr(f, "severity"):
                sev = str(getattr(f, "severity", "info")).lower()
            rank = severity_rank.get(sev, 1)
            if rank > max_rank:
                max_rank = rank

        rank_to_sev = {5: "critical", 4: "high", 3: "medium", 2: "low", 1: "info"}
        overall_severity = rank_to_sev.get(max_rank, "info")

        summary = "Merged review combining static analysis and LLM reasoning."
        if isinstance(llm_review, dict) and llm_review.get("review_summary"):
            summary = llm_review["review_summary"]
        elif hasattr(llm_review, "review_summary"):
            summary = getattr(llm_review, "review_summary")

        confidence = 0.85
        if isinstance(llm_review, dict) and "confidence" in llm_review:
            confidence = float(llm_review["confidence"])
        elif hasattr(llm_review, "confidence"):
            confidence = float(getattr(llm_review, "confidence"))

        return MergedReview(
            summary=summary,
            overall_severity=overall_severity,
            findings=unique_findings,
            confidence_score=confidence,
            priority="high" if max_rank >= 4 else "medium" if max_rank == 3 else "low",
            sources=["StaticAnalysis", "LLMReview"],
            metadata={"total_merged": len(unique_findings)}
        )
