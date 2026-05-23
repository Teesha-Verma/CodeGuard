import json
from typing import Dict, Any, Optional
from app.llm.llm_client import LLMClient

ROOT_CAUSE_SYSTEM_PROMPT = """You are a grounded Root Cause Analysis engine.
Your task is to analyze the provided deterministic static-analysis finding and localized code context to generate highly precise explanations.

CRITICAL ENGINEERING CONSTRAINTS:
1. MAX DEPTH: Your ENTIRE explanation MUST be a maximum of 3 sentences total across all fields. Keep it localized, concise, and professional. No essays.
2. EVIDENCE ANCHORING: You must ONLY refer to the facts provided in the evidence (AST nodes, linter rules, or structural metadata). Never speculate or warn about imaginary bugs.
3. STRUCTURED REASONING: Your explanations must follow this strict framework:
   - WHY: The underlying code behavior that creates the hazard (root_cause).
   - WHEN: The exact runtime condition that triggers it (trigger_condition).
   - WHAT + HOW: The consequence of triggering it AND a concise, actionable, structural correction (fix).
4. OUTPUT FORMAT: You must return a valid JSON object in exactly this format:
{
  "root_cause": "<WHY — concise explanation of the underlying code behavior creating the hazard>",
  "trigger_condition": "<WHEN — the exact runtime condition that triggers the issue>",
  "fix": "<WHAT + HOW — consequence of the issue AND a concise structural correction>",
  "patch": "<minimal code patch replacing the bad lines, or empty string if not applicable>",
  "issue_type": "<runtime_logic_error|security|complexity|code_smell|style>"
}
"""

class RootCauseEngine:
    """Generates concise, grounded explanations and fixes for deterministic findings."""
    
    def __init__(self, review_id: str):
        self.llm_client = LLMClient(review_id=review_id)

    def analyze_finding(self, finding: Dict[str, Any], aggregated_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls the LLM with localized context and pre-identified evidence to perform root-cause reasoning.

        Phase 4 upgrade: enriches the evidence payload with AST structure contexts
        (nesting depth, recursion, shadowing, test context, ast_rules_findings)
        and enforces WHY/WHEN/WHAT/HOW structured reasoning via the upgraded prompt.
        """
        # Find the specific code snippet around the target line
        line_no = finding.get("line", 1)
        code_context = aggregated_context.get("code_context", [])
        
        # Localize target snippet
        localized_code = ""
        for snippet in code_context:
            snippet_lines = snippet.get("code", "").splitlines()
            start_line = snippet.get("start_line", 1)
            # Check if line_no is near or within this snippet
            if start_line <= line_no <= start_line + len(snippet_lines) + 5:
                localized_code = snippet.get("code", "")
                break

        # ── Phase 4: Enrich evidence payload with AST structure contexts ──
        ast_struct = aggregated_context.get("ast_structural_metadata", {})
        if not isinstance(ast_struct, dict):
            ast_struct = {}

        # Extract relevant function context for the target line
        function_context = None
        for func in ast_struct.get("functions", []):
            if func.get("start_line", 0) <= line_no <= func.get("end_line", 0):
                function_context = {
                    "name": func.get("name"),
                    "is_async": func.get("is_async", False),
                    "is_recursive": func.get("is_recursive", False),
                    "has_docstring": func.get("has_docstring", False),
                    "args": func.get("args", []),
                }
                break

        # Extract nesting depth context for the target line
        nesting_context = None
        for cs in ast_struct.get("control_structures", []):
            if cs.get("line") == line_no:
                nesting_context = {
                    "type": cs.get("type"),
                    "nesting_depth": cs.get("nesting_depth", 0),
                }
                break

        # Extract relevant AST rule findings for the target line
        relevant_ast_rules = []
        for rule_finding in ast_struct.get("ast_rules_findings", []):
            if rule_finding.get("line") == line_no:
                relevant_ast_rules.append({
                    "rule": rule_finding.get("rule_name"),
                    "summary": rule_finding.get("message"),
                })

        # ── Build enriched payload ────────────────────────────────
        payload = {
            "finding": {
                "line": line_no,
                "issue": finding.get("issue"),
                "severity": finding.get("severity"),
                "sources": finding.get("sources", []),
                "evidence": finding.get("evidence", {})
            },
            "file_path": aggregated_context.get("file_path", ""),
            "localized_code": localized_code,
            # Phase 4: enriched structural context
            "structural_context": {
                "function": function_context,
                "nesting": nesting_context,
                "ast_rule_detections": relevant_ast_rules,
            }
        }
        
        user_content = json.dumps(payload, indent=2)
        response = self.llm_client.generate_structured(ROOT_CAUSE_SYSTEM_PROMPT, user_content)
        
        if response:
            # Enforce max 3 sentences constraint on root_cause programmatically
            rc_text = response.get("root_cause", "")
            sentences = [s.strip() for s in rc_text.split(".") if s.strip()]
            if len(sentences) > 3:
                response["root_cause"] = ". ".join(sentences[:3]) + "."

            # Enforce max 3 sentences constraint on fix programmatically
            fix_text = response.get("fix", "")
            fix_sentences = [s.strip() for s in fix_text.split(".") if s.strip()]
            if len(fix_sentences) > 3:
                response["fix"] = ". ".join(fix_sentences[:3]) + "."
                
            return response
            
        return {
            "root_cause": f"Static analysis identified a code issue: {finding.get('issue')}.",
            "trigger_condition": "Triggers during execution of line.",
            "fix": "Please review the highlighted line and fix according to standard practices.",
            "patch": "",
            "issue_type": finding.get("issue_type", "code_smell")
        }
