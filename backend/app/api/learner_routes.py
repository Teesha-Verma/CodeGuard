"""
CodeGuard V2 — Contextual Learner Mode Routes.

Generates grounded educational explanations and interactive quizzes
based on real static analysis findings and RAG security knowledge.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, status

from app.analysis.RAG.knowledge_retrieval_service import KnowledgeRetrievalService
from app.api.schemas import (
    LearnerFindingRequest,
    LearnerFindingResponse,
    QuizModel,
)
from app.llm.service import LLMService
from app.storage.review_store import ReviewStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/learn", tags=["Learner"])


@router.post("/finding", response_model=LearnerFindingResponse)
def learn_from_finding(request: LearnerFindingRequest) -> LearnerFindingResponse:
    """
    Generate grounded educational lesson and quiz for a specific code finding.
    Uses server-side authoritative finding record + RAG knowledge retrieval.
    """
    review_store = ReviewStore.get_instance()
    report = review_store.get_report(request.review_id) if request.review_id else None
    target_line = request.finding_line or request.line or 1

    # Locate finding
    matched_issue = None
    file_code_snippet = request.code_snippet or ""
    if report and request.file_path:
        for file_rep in report.file_reports:
            fp = file_rep.get("file_path", "") if isinstance(file_rep, dict) else getattr(file_rep, "file_path", "")
            if fp == request.file_path:
                issues = file_rep.get("issues", []) if isinstance(file_rep, dict) else getattr(file_rep, "issues", [])
                for iss in issues:
                    iline = iss.get("line", 0) if isinstance(iss, dict) else getattr(iss, "line", 0)
                    if iline == target_line:
                        matched_issue = iss
                        break
                fc = file_rep.get("file_content", "") if isinstance(file_rep, dict) else getattr(file_rep, "file_content", "")
                if fc:
                    lines = fc.splitlines()
                    start = max(0, target_line - 5)
                    end = min(len(lines), target_line + 5)
                    file_code_snippet = "\n".join(lines[start:end])
                break

    # Build normalized finding dict
    ititle = matched_issue.get("issue", "") if isinstance(matched_issue, dict) else (getattr(matched_issue, "issue", "") if matched_issue else "")
    isev = matched_issue.get("severity", "high") if isinstance(matched_issue, dict) else (getattr(matched_issue, "severity", "high") if matched_issue else "high")
    iroot = matched_issue.get("root_cause", "") if isinstance(matched_issue, dict) else (getattr(matched_issue, "root_cause", "") if matched_issue else "")
    itrig = matched_issue.get("trigger_condition", "") if isinstance(matched_issue, dict) else (getattr(matched_issue, "trigger_condition", "") if matched_issue else "")
    ifix = matched_issue.get("fix", "") if isinstance(matched_issue, dict) else (getattr(matched_issue, "fix", "") if matched_issue else "")
    ipatch = matched_issue.get("patch", "") if isinstance(matched_issue, dict) else (getattr(matched_issue, "patch", "") if matched_issue else "")
    istandards = matched_issue.get("standards", []) if isinstance(matched_issue, dict) else (getattr(matched_issue, "standards", []) if matched_issue else [])
    icat = (matched_issue.get("category") or matched_issue.get("issue_type")) if isinstance(matched_issue, dict) else ((getattr(matched_issue, "category", None) or getattr(matched_issue, "issue_type", None)) if matched_issue else None)

    finding_dict = {
        "issue": ititle or (request.issue_text or "Security finding"),
        "severity": isev,
        "line": target_line,
        "file": request.file_path or "snippet.py",
        "root_cause": iroot,
        "trigger_condition": itrig,
        "fix": ifix,
        "patch": ipatch,
        "standards": istandards,
        "category": icat or (request.category or "Security"),
    }

    # 1. RAG Knowledge retrieval
    rag_context = ""
    try:
        rag_service = KnowledgeRetrievalService.get_instance()
        assembled = rag_service.retrieve_for_finding(finding_dict, top_k=2)
        if assembled and assembled.formatted_prompt_context:
            rag_context = assembled.formatted_prompt_context
    except Exception as e:
        logger.warning(f"RAG retrieval skipped for learner: {e}")

    # 2. Try LLM structured generation
    system_prompt = (
        "You are an elite application security educator. "
        "Generate a structured educational lesson and a multiple-choice quiz for the provided code finding. "
        "Respond ONLY with a valid JSON object matching this schema:\n"
        "{\n"
        '  "concept": "Core security concept name",\n'
        '  "what_happened": "Exact description of what happened in the user\'s code",\n'
        '  "why_it_matters": "Security impact and attack scenarios",\n'
        '  "evidence": "How the issue was detected",\n'
        '  "how_to_fix": "Clear instructions on how to remediate",\n'
        '  "safer_implementation": "Python code snippet demonstrating the safe pattern",\n'
        '  "key_takeaway": "One-sentence memorable rule of thumb",\n'
        '  "quiz": {\n'
        '    "question": "Realistic question testing understanding of this specific flaw",\n'
        '    "options": ["Option A", "Option B", "Option C", "Option D"],\n'
        '    "correct_index": 1,\n'
        '    "explanation": "Why the correct option is safe and the others are vulnerable"\n'
        "  }\n"
        "}"
    )

    user_content = (
        f"Finding: {finding_dict['issue']}\n"
        f"File: {finding_dict['file']}:{finding_dict['line']}\n"
        f"Severity: {finding_dict['severity']}\n"
        f"Root Cause: {finding_dict['root_cause']}\n"
        f"Fix Suggestion: {finding_dict['fix']}\n"
        f"Standards: {', '.join(finding_dict['standards'])}\n"
    )
    if file_code_snippet:
        user_content += f"Surrounding Code:\n```python\n{file_code_snippet}\n```\n"
    if rag_context:
        user_content += f"RAG Security Knowledge:\n{rag_context}\n"

    llm_service = LLMService()
    structured = None
    try:
        structured = llm_service.generate_structured(
            system_prompt=system_prompt,
            user_content=user_content,
            review_id=request.review_id or "learn"
        )
    except Exception as e:
        logger.warning(f"LLM learner generation failed: {e}")

    if structured and "concept" in structured and "quiz" in structured:
        quiz_data = structured.get("quiz", {})
        correct_idx = quiz_data.get("correct_index", quiz_data.get("correct_option", 0))
        concept_val = structured.get("concept", finding_dict["category"])
        what_val = structured.get("what_happened", finding_dict["issue"])
        why_val = structured.get("why_it_matters", "Leaves system exposed to malicious manipulation.")
        fix_val = structured.get("how_to_fix", finding_dict["fix"] or "Use parameterized interfaces.")
        safe_val = structured.get("safer_implementation", "# Safe pattern\n")
        return LearnerFindingResponse(
            concept_title=concept_val,
            concept=concept_val,
            cwe=finding_dict["standards"][0] if finding_dict["standards"] else "CWE-General",
            owasp="OWASP Top 10",
            concept_summary=what_val,
            what_happened_in_code=what_val,
            what_happened=what_val,
            why_it_matters=why_val,
            impact=why_val,
            evidence_breakdown=structured.get("evidence", f"Detected at {request.file_path}:{target_line}"),
            evidence=structured.get("evidence", f"Detected at {request.file_path}:{target_line}"),
            how_to_fix=fix_val,
            good_code=safe_val,
            safer_implementation=safe_val,
            bad_code=file_code_snippet or "# Vulnerable pattern",
            key_takeaway=structured.get("key_takeaway", "Never trust unvalidated input."),
            quiz=QuizModel(
                question=quiz_data.get("question", "How should this vulnerability be resolved?"),
                options=quiz_data.get("options", [
                    "Use parameterized queries / safe APIs",
                    "Add a regex filter",
                    "Wrap in a try-catch block",
                    "Encode input with base64"
                ]),
                correct_option=correct_idx,
                correct_index=correct_idx,
                explanation=quiz_data.get("explanation", "Parameterized queries ensure user input is treated as literal data.")
            ),
            standards=finding_dict["standards"]
        )

    # 3. Deterministic fallback grounded in the finding and security rules
    return _build_deterministic_lesson(finding_dict, file_code_snippet)


def _build_deterministic_lesson(finding: Dict[str, Any], snippet: str) -> LearnerFindingResponse:
    """Provides high quality, grounded educational response when LLMs are offline."""
    issue_text = finding.get("issue", "").lower()
    standards = finding.get("standards", [])

    if "sql" in issue_text:
        return LearnerFindingResponse(
            concept_title="SQL Injection (CWE-89 / OWASP A03)",
            concept="SQL Injection (CWE-89 / OWASP A03)",
            cwe="CWE-89",
            owasp="A03:2021-Injection",
            concept_summary="Dynamic string concatenation constructs a database query, treating user strings as SQL commands.",
            what_happened_in_code=(
                f"Dynamic string concatenation was used to construct a database query at line {finding.get('line', 1)}. "
                "The database interpreter treats user-supplied strings as executable SQL commands."
            ),
            what_happened=(
                f"Dynamic string concatenation was used to construct a database query at line {finding.get('line', 1)}. "
                "The database interpreter treats user-supplied strings as executable SQL commands."
            ),
            why_it_matters=(
                "An attacker can inject arbitrary SQL fragments (e.g. `' OR '1'='1`) to bypass authentication, "
                "dump sensitive tables, modify database contents, or execute administrative operations."
            ),
            impact="Data exposure, authentication bypass, data loss, and possible host takeover.",
            evidence_breakdown=f"Flagged by CodeGuard AST BinOp / JoinedStr visitor on line {finding.get('line', 1)}.",
            evidence=f"Flagged by CodeGuard AST BinOp / JoinedStr visitor on line {finding.get('line', 1)}.",
            how_to_fix=(
                "Use parameterized query placeholders (%s, :param, or ? depending on driver) or an ORM query builder. "
                "Never concatenate variables directly into SQL statements."
            ),
            good_code=(
                "# Secure Parameterization:\n"
                "cursor.execute(\"SELECT * FROM users WHERE username = %s\", (user_input,))\n"
                "records = cursor.fetchall()"
            ),
            safer_implementation=(
                "# Secure Parameterization:\n"
                "cursor.execute(\"SELECT * FROM users WHERE username = %s\", (user_input,))\n"
                "records = cursor.fetchall()"
            ),
            bad_code=snippet or "# query = f'SELECT * FROM users WHERE username={user_input}'",
            key_takeaway="Separate code from data: parameter placeholders treat user input purely as literal values.",
            quiz=QuizModel(
                question="Which implementation completely eliminates SQL injection vulnerability?",
                options=[
                    "cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
                    "cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
                    "cursor.execute('SELECT * FROM users WHERE id=' + str(user_id))",
                    "cursor.execute('SELECT * FROM users WHERE id={}'.format(user_id))"
                ],
                correct_option=1,
                correct_index=1,
                explanation="The database driver parameterizes the tuple argument separately from query syntax, preventing payload execution."
            ),
            standards=standards or ["CWE-89", "OWASP-A03:2021"]
        )

    if "command" in issue_text or "subprocess" in issue_text:
        return LearnerFindingResponse(
            concept_title="Command Injection (CWE-78)",
            concept="Command Injection (CWE-78)",
            cwe="CWE-78",
            owasp="A03:2021-Injection",
            concept_summary="External user input is passed directly to an operating system shell without sanitization.",
            what_happened_in_code=(
                f"Line {finding.get('line', 1)} executes shell commands with untrusted input using shell=True or string concatenation."
            ),
            what_happened=(
                f"Line {finding.get('line', 1)} executes shell commands with untrusted input using shell=True or string concatenation."
            ),
            why_it_matters="Allows attackers to execute arbitrary system commands with the privileges of the web application.",
            impact="Remote code execution and total host takeover.",
            evidence_breakdown=f"Flagged subprocess call with shell=True or formatted argument string on line {finding.get('line', 1)}.",
            evidence=f"Flagged subprocess call with shell=True or formatted argument string on line {finding.get('line', 1)}.",
            how_to_fix="Pass command arguments as a list with shell=False, or use dedicated standard library APIs.",
            good_code=(
                "# Secure command execution:\n"
                "subprocess.run(['ping', '-c', '1', target_host], shell=False, check=True)"
            ),
            safer_implementation=(
                "# Secure command execution:\n"
                "subprocess.run(['ping', '-c', '1', target_host], shell=False, check=True)"
            ),
            bad_code=snippet or "# subprocess.run(f'ping -c 1 {target_host}', shell=True)",
            key_takeaway="Never invoke a system shell unless strictly necessary; pass argument lists directly to the executable.",
            quiz=QuizModel(
                question="Why is `subprocess.run(['ls', dirname], shell=False)` safer than `shell=True`?",
                options=[
                    "It runs faster by skipping the shell process",
                    "It prevents shell metacharacters like `;` and `|` from being interpreted",
                    "It runs the command with root privileges",
                    "It automatically validates filenames"
                ],
                correct_option=1,
                correct_index=1,
                explanation="Without an intermediate shell, arguments are passed directly to the OS exec system call without meta-character evaluation."
            ),
            standards=standards or ["CWE-78"]
        )

    # General fallback
    return LearnerFindingResponse(
        concept_title=finding.get("category") or "Secure Software Engineering",
        concept=finding.get("category") or "Secure Software Engineering",
        cwe="CWE-General",
        owasp="OWASP-General",
        concept_summary=f"CodeGuard detected potentially hazardous logic: '{finding.get('issue')}'.",
        what_happened_in_code=f"CodeGuard detected potentially hazardous logic: '{finding.get('issue')}'.",
        what_happened=f"CodeGuard detected potentially hazardous logic: '{finding.get('issue')}'.",
        why_it_matters="Unsanitized inputs and unhandled edge cases can result in runtime exceptions or security exploits.",
        impact="Software instability and potential exploit surface.",
        evidence_breakdown=finding.get("root_cause") or f"Detected at line {finding.get('line', 1)}.",
        evidence=finding.get("root_cause") or f"Detected at line {finding.get('line', 1)}.",
        how_to_fix=finding.get("fix") or "Apply input validation, boundary checking, and use safe standard library methods.",
        good_code=finding.get("patch") or "# Use validated input and defensive programming patterns.",
        safer_implementation=finding.get("patch") or "# Use validated input and defensive programming patterns.",
        bad_code=snippet or "# Potentially vulnerable code pattern",
        key_takeaway="Validate all inputs at system boundaries and adhere to principle of least privilege.",
        quiz=QuizModel(
            question="What is the primary defense against injection and boundary errors?",
            options=[
                "Validating and parameterizing inputs at boundaries",
                "Encrypting the local database",
                "Increasing web server memory",
                "Hiding server error messages"
            ],
            correct_option=0,
            correct_index=0,
            explanation="Validating inputs against strict allowlists and using parameterized abstractions prevents untrusted data manipulation."
        ),
        standards=standards or ["CWE Security"]
    )
