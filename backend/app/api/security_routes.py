"""
CodeGuard V2 — Security Health and Risk Telemetry Routes.

Computes deterministic security health scores, risk rankings,
and vulnerability posture across all reviewed code.
"""
from __future__ import annotations

import logging
from typing import Dict, List

from fastapi import APIRouter

from app.api.schemas import (
    FileRiskItem,
    RepositoryRiskResponse,
    SecurityHealthResponse,
)
from app.storage.review_store import ReviewStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/security", tags=["Security"])


@router.get("/health", response_model=SecurityHealthResponse)
def get_security_health() -> SecurityHealthResponse:
    """
    Computes overall security health score across all historical reviews
    using a deterministic, explainable penalty formula.
    """
    review_store = ReviewStore.get_instance()
    summaries, total_count = review_store.list_reports(limit=200)

    total_issues = 0
    critical_issues = 0
    high_issues = 0
    medium_issues = 0
    low_issues = 0
    style_issues = 0
    category_breakdown: Dict[str, int] = {}

    for summary in summaries:
        # Load full report to aggregate categories and counts
        rep = review_store.get_report(summary.review_id)
        if not rep:
            continue

        stats = rep.summary_stats
        if isinstance(stats, dict):
            by_sev = stats.get("by_severity", {})
            critical_issues += by_sev.get("critical", 0) if isinstance(by_sev, dict) else getattr(by_sev, "critical", 0)
            high_issues += by_sev.get("high", 0) if isinstance(by_sev, dict) else getattr(by_sev, "high", 0)
            medium_issues += by_sev.get("medium", 0) if isinstance(by_sev, dict) else getattr(by_sev, "medium", 0)
            low_issues += by_sev.get("low", 0) if isinstance(by_sev, dict) else getattr(by_sev, "low", 0)
            style_issues += stats.get("style_findings", 0)
            total_issues += stats.get("total_issues", 0)
        else:
            by_sev = getattr(stats, "by_severity", {})
            critical_issues += by_sev.get("critical", 0) if isinstance(by_sev, dict) else getattr(by_sev, "critical", 0)
            high_issues += by_sev.get("high", 0) if isinstance(by_sev, dict) else getattr(by_sev, "high", 0)
            medium_issues += by_sev.get("medium", 0) if isinstance(by_sev, dict) else getattr(by_sev, "medium", 0)
            low_issues += by_sev.get("low", 0) if isinstance(by_sev, dict) else getattr(by_sev, "low", 0)
            style_issues += getattr(stats, "style_findings", 0)
            total_issues += getattr(stats, "total_issues", 0)

        file_reports = rep.file_reports or []
        for file_rep in file_reports:
            issues = file_rep.get("issues", []) if isinstance(file_rep, dict) else getattr(file_rep, "issues", [])
            for iss in issues:
                cat = (
                    (iss.get("category") or iss.get("issue_type"))
                    if isinstance(iss, dict)
                    else (getattr(iss, "category", None) or getattr(iss, "issue_type", None) or "Security")
                ) or "Security"
                category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

    # Deterministic Formula: 100 - (15*crit + 8*high + 3*med + 1*low)
    if total_count == 0:
        score = 100
    else:
        deductions = (
            (15 * critical_issues)
            + (8 * high_issues)
            + (3 * medium_issues)
            + (1 * low_issues)
        )
        score = max(0, min(100, 100 - deductions))

    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    return SecurityHealthResponse(
        security_score=score,
        score=score,
        grade=grade,
        total_reviews=total_count,
        total_issues=total_issues,
        critical_count=critical_issues,
        critical_issues=critical_issues,
        high_count=high_issues,
        high_issues=high_issues,
        medium_count=medium_issues,
        medium_issues=medium_issues,
        low_count=low_issues,
        low_issues=low_issues,
        style_count=style_issues,
        style_issues=style_issues,
        categories=category_breakdown,
        category_breakdown=category_breakdown,
        formula="score = max(0, min(100, 100 - (15*crit + 8*high + 3*med + 1*low)))"
    )


@router.get("/risk", response_model=RepositoryRiskResponse)
def get_security_risk() -> RepositoryRiskResponse:
    """
    Computes file-level risk rankings and vulnerability hotspots
    derived from authoritative static analysis findings.
    """
    review_store = ReviewStore.get_instance()
    summaries, _ = review_store.list_reports(limit=200)

    file_stats: Dict[str, Dict[str, int]] = {}
    category_counts: Dict[str, int] = {}
    any_critical = False
    any_high = False
    any_medium = False

    for summary in summaries:
        rep = review_store.get_report(summary.review_id)
        if not rep:
            continue

        file_reports = rep.file_reports or []
        for file_rep in file_reports:
            path = file_rep.get("file_path", "") if isinstance(file_rep, dict) else getattr(file_rep, "file_path", "")
            if not path:
                continue
            if path not in file_stats:
                file_stats[path] = {
                    "critical": 0,
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "total": 0
                }

            issues = file_rep.get("issues", []) if isinstance(file_rep, dict) else getattr(file_rep, "issues", [])
            for iss in issues:
                cat = (
                    (iss.get("category") or iss.get("issue_type"))
                    if isinstance(iss, dict)
                    else (getattr(iss, "category", None) or getattr(iss, "issue_type", None) or "Security")
                ) or "Security"
                category_counts[cat] = category_counts.get(cat, 0) + 1

                file_stats[path]["total"] += 1
                sev = (iss.get("severity", "") if isinstance(iss, dict) else getattr(iss, "severity", "")).lower()
                if sev == "critical":
                    file_stats[path]["critical"] += 1
                    any_critical = True
                elif sev == "high":
                    file_stats[path]["high"] += 1
                    any_high = True
                elif sev == "medium":
                    file_stats[path]["medium"] += 1
                    any_medium = True
                else:
                    file_stats[path]["low"] += 1

    # Score each file: 10*crit + 5*high + 2*med + 1*low
    ranked_files: List[FileRiskItem] = []
    for path, counts in file_stats.items():
        risk_score = (
            (10 * counts["critical"])
            + (5 * counts["high"])
            + (2 * counts["medium"])
            + (1 * counts["low"])
        )
        ranked_files.append(
            FileRiskItem(
                file_path=path,
                risk_score=risk_score,
                critical=counts["critical"],
                critical_count=counts["critical"],
                high=counts["high"],
                high_count=counts["high"],
                medium=counts["medium"],
                medium_count=counts["medium"],
                low=counts["low"],
                low_count=counts["low"],
                total=counts["total"],
                total_count=counts["total"]
            )
        )

    high_risk_count = sum(1 for f in ranked_files if f.critical > 0 or f.high > 0)
    med_risk_count = sum(1 for f in ranked_files if f.critical == 0 and f.high == 0 and f.medium > 0)
    low_risk_count = sum(1 for f in ranked_files if f.critical == 0 and f.high == 0 and f.medium == 0 and f.low > 0)

    if any_critical:
        overall = "critical"
    elif any_high:
        overall = "high"
    elif any_medium:
        overall = "medium"
    else:
        overall = "low"

    return RepositoryRiskResponse(
        overall_risk=overall,
        ranked_files=ranked_files,
        top_categories=category_counts,
        formula="file_risk = (10 * critical) + (5 * high) + (2 * medium) + (1 * low)",
        files=ranked_files,
        high_risk_count=high_risk_count,
        medium_risk_count=med_risk_count,
        low_risk_count=low_risk_count,
    )

