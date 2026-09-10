"""
CodeGuard V2 — Context-Aware AI Assistant Routes.

Provides conversational code security guidance leveraging Groq (primary)
with Gemini (fallback), grounded in authoritative review and finding context.
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.api.schemas import (
    AssistantChatRequest,
    AssistantChatResponse,
)
from app.llm.models import LLMRequest, LLMResponse
from app.llm.service import LLMService
from app.storage.review_store import ReviewStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/chat", response_model=AssistantChatResponse)
def chat_with_assistant(request: AssistantChatRequest) -> AssistantChatResponse:
    """
    Context-aware conversational code review assistant.
    Grounded in server-side authoritative finding and review records.
    """
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one message is required."
        )

    last_user_message = next(
        (m.content for m in reversed(request.messages) if m.role.lower() == "user"),
        ""
    )

    # 1. Authoritative context resolution
    finding_context_str = ""
    code_context_str = ""
    review_context_str = ""
    context_label = "General Security Context"

    review_store = ReviewStore.get_instance()
    report = review_store.get_report(request.review_id) if request.review_id else None

    target_line = request.finding_line or request.line

    if report:
        stats = report.summary_stats
        by_sev = stats.get("by_severity", {}) if isinstance(stats, dict) else getattr(stats, "by_severity", {})
        crit = by_sev.get("critical", 0) if isinstance(by_sev, dict) else getattr(by_sev, "critical", 0)
        high = by_sev.get("high", 0) if isinstance(by_sev, dict) else getattr(by_sev, "high", 0)
        med = by_sev.get("medium", 0) if isinstance(by_sev, dict) else getattr(by_sev, "medium", 0)
        tot = stats.get("total_issues", 0) if isinstance(stats, dict) else getattr(stats, "total_issues", 0)
        review_context_str = (
            f"Review ID: {report.review_id}\n"
            f"Repository: {getattr(report, 'repo_url', None) or 'Snippet'}\n"
            f"Total Issues: {tot}\n"
            f"Critical: {crit}, High: {high}, Medium: {med}\n"
        )
        context_label = f"Review {report.review_id[:8]}"

        # Locate targeted finding
        if request.file_path and report.file_reports:
            for file_rep in report.file_reports:
                fp = file_rep.get("file_path", "") if isinstance(file_rep, dict) else getattr(file_rep, "file_path", "")
                if fp == request.file_path:
                    fc = file_rep.get("file_content", "") if isinstance(file_rep, dict) else getattr(file_rep, "file_content", "")
                    # Extract code slice if file content available
                    if fc and target_line:
                        lines = fc.splitlines()
                        start = max(0, target_line - 8)
                        end = min(len(lines), target_line + 8)
                        code_slice = "\n".join(
                            f"{i+1:4d} | {lines[i]}" for i in range(start, end)
                        )
                        code_context_str = f"File: {request.file_path} (Lines {start+1}-{end}):\n{code_slice}\n"

                    # Find finding
                    if target_line:
                        issues = file_rep.get("issues", []) if isinstance(file_rep, dict) else getattr(file_rep, "issues", [])
                        for issue in issues:
                            iline = issue.get("line", 0) if isinstance(issue, dict) else getattr(issue, "line", 0)
                            if iline == target_line:
                                ititle = issue.get("issue", "") if isinstance(issue, dict) else getattr(issue, "issue", "")
                                isev = issue.get("severity", "medium") if isinstance(issue, dict) else getattr(issue, "severity", "medium")
                                icat = (issue.get("category") or issue.get("issue_type")) if isinstance(issue, dict) else (getattr(issue, "category", None) or getattr(issue, "issue_type", None))
                                iroot = issue.get("root_cause", "") if isinstance(issue, dict) else getattr(issue, "root_cause", "")
                                ifix = issue.get("fix", "") if isinstance(issue, dict) else getattr(issue, "fix", "")
                                ipatch = issue.get("patch", "") if isinstance(issue, dict) else getattr(issue, "patch", "")
                                istandards = issue.get("standards", []) if isinstance(issue, dict) else getattr(issue, "standards", [])
                                idataflow = issue.get("dataflow_path", []) if isinstance(issue, dict) else getattr(issue, "dataflow_path", [])

                                finding_context_str = (
                                    f"Target Finding: {ititle}\n"
                                    f"Severity: {str(isev).upper()}\n"
                                    f"File: {request.file_path}:{iline}\n"
                                    f"Category: {icat or 'Security'}\n"
                                    f"Root Cause: {iroot or 'Dynamic input evaluation'}\n"
                                    f"Remediation: {ifix or 'Use safe, parameterized APIs'}\n"
                                    f"Suggested Patch:\n{ipatch or 'N/A'}\n"
                                    f"Standards: {', '.join(istandards) if istandards else 'CWE'}\n"
                                )
                                if idataflow:
                                    finding_context_str += f"Taint Flow: {' -> '.join(idataflow)}\n"
                                context_label = f"Finding at line {iline}"
                                break
                    break

    # 2. Build concise, token-efficient system and user prompt
    system_prompt = (
        "You are CodeGuard Assistant, an elite application security expert and code reviewer. "
        "Provide direct, concise, and technically rigorous answers to developer questions. "
        "Reference specific line numbers, AST patterns, taint flow, and CWE/OWASP standards where applicable. "
        "Always provide safe code examples when remediation is requested. "
        "Keep responses focused, actionable, and under 300 words unless extensive explanation is requested."
    )

    prompt_context_parts = []
    if review_context_str:
        prompt_context_parts.append(f"### Review Overview\n{review_context_str}")
    if finding_context_str:
        prompt_context_parts.append(f"### Authoritative Finding Context\n{finding_context_str}")
    if code_context_str:
        prompt_context_parts.append(f"### Source Code\n```python\n{code_context_str}```")
    if getattr(request, "context", None):
        prompt_context_parts.append(f"### Additional Context\n{request.context}")

    full_context = "\n\n".join(prompt_context_parts)

    user_prompt = (
        f"{full_context}\n\n"
        f"Developer Question: {last_user_message}"
    ) if full_context else last_user_message

    # 3. Call multi-provider LLM service
    llm_service = LLMService()
    provider_name = None
    model_name = None
    fallback_used = False
    reply_text = ""

    try:
        llm_req = LLMRequest(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=1024,
            response_format="text",
            timeout=25.0,
            metadata={"review_id": request.review_id or "chat"}
        )

        response: LLMResponse = llm_service.router.route_request(
            request=llm_req,
            structured=False
        )

        if response.is_success and response.raw_text:
            reply_text = response.raw_text.strip()
            provider_name = response.provider
            model_name = response.model
            fallback_used = response.fallback_used
    except Exception as e:
        logger.warning(f"Assistant LLM call failed or offline: {e}")

    # 4. Deterministic fallback if LLM is offline or unconfigured
    if not reply_text:
        reply_text = _generate_deterministic_reply(
            query=last_user_message,
            finding_context=finding_context_str,
            report=report,
            line=target_line,
            file_path=request.file_path
        )
        provider_name = "codeguard-deterministic"
        model_name = "ast-security-rules"

    return AssistantChatResponse(
        message=reply_text,
        reply=reply_text,
        provider=provider_name or "codeguard",
        model=model_name or "ast-security-rules",
        fallback_used=fallback_used,
        trace_id="assistant_chat_trace",
        context_used=context_label
    )


def _generate_deterministic_reply(
    query: str,
    finding_context: str,
    report: Optional[object],
    line: Optional[int],
    file_path: Optional[str]
) -> str:
    """Deterministic security reasoning when external LLM providers are unavailable."""
    q = query.lower()

    if "fix" in q or "remediat" in q or "solve" in q:
        if finding_context and "Remediation:" in finding_context:
            for part in finding_context.splitlines():
                if part.startswith("Remediation:"):
                    return (
                        f"### Remediation Plan\n\n"
                        f"{part.replace('Remediation: ', '')}\n\n"
                        f"**Key Recommendation**: Always sanitize and parameterize user inputs at system boundaries "
                        f"to prevent control-flow manipulation. You can test your fix directly in the **Fix Playground**."
                    )
        return "To remediate this issue, replace direct string interpolation with parameterized queries or validated structural types."

    if "why" in q or "explain" in q or "impact" in q:
        if finding_context:
            return (
                f"### Analysis\n\n"
                f"{finding_context}\n\n"
                f"This pattern violates security best practices because external data flows directly into "
                f"a sensitive execution sink without validation."
            )
        return "CodeGuard flagged this pattern because untrusted inputs flow directly into execution sinks."

    if "dataflow" in q or "taint" in q:
        if finding_context and "Taint Flow:" in finding_context:
            for part in finding_context.splitlines():
                if part.startswith("Taint Flow:"):
                    return f"### Dataflow Analysis\n\n{part}\n\nCodeGuard detected an unbroken propagation path."
        return "No taint path was recorded for this finding; detection was performed via structural AST pattern matching."

    return (
        f"I am CodeGuard Assistant. I analyze static AST rules, dataflow taint traces, and security standards.\n\n"
        f"You can ask me to explain findings, propose remediations, inspect dataflow paths, or summarize pull requests."
    )
