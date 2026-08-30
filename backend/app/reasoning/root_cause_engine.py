import json
from typing import Dict, Any, Optional
from app.llm.llm_client import LLMClient
from app.core.config import get_settings

ROOT_CAUSE_SYSTEM_PROMPT = """You are a grounded Root Cause Analysis engine.
Your task is to analyze the provided deterministic static-analysis finding, structural context, data flow traces, and retrieved official knowledge rules to generate highly precise explanations.

CRITICAL ENGINEERING CONSTRAINTS:
1. MAX DEPTH: Your ENTIRE explanation MUST be a maximum of 3 sentences total across all fields. Keep it localized, concise, and professional. No essays.
2. EVIDENCE ANCHORING: You must ONLY refer to the facts provided in the evidence (AST nodes, linter rules, data flow traces, or retrieved knowledge standards). Never speculate or warn about imaginary bugs.
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
    """Generates concise, grounded explanations and fixes for deterministic findings backed by static, flow, and RAG evidence."""

    def __init__(self, review_id: str):
        self.review_id = review_id or "default"
        self.llm_client = LLMClient(review_id=self.review_id)
        self.settings = get_settings()

    def analyze_finding(self, finding: Dict[str, Any], aggregated_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Calls the LLM with localized context, pre-identified evidence, and retrieved RAG knowledge to perform root-cause reasoning.
        """
        line_no = finding.get("line", 1)
        file_path = aggregated_context.get("file_path", "")

        # Extract bounded, localized source code around target line
        localized_code = self._extract_localized_code(aggregated_context, line_no)

        # Enrich evidence payload with AST structure contexts
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

        # Extract CFG, Call Graph, and Dataflow contexts
        cfg_context = aggregated_context.get("cfg_analysis", {})
        call_graph_context = aggregated_context.get("call_graph_analysis", {})
        dataflow_evidence = finding.get("evidence", {}).get("dataflow_findings", [])
        retrieved_knowledge = aggregated_context.get("retrieved_knowledge", "")

        # Build enriched payload with explicit fields required by Problem 8 & 9
        payload = {
            "file_path": file_path,
            "target_line": line_no,
            "finding": {
                "line": line_no,
                "issue": finding.get("issue"),
                "severity": finding.get("severity"),
                "confidence": finding.get("confidence", 0.8),
                "issue_category": finding.get("issue_category", "runtime logic risks"),
                "sources": finding.get("sources", []),
                "detection_sources": finding.get("sources", []),
                "evidence": finding.get("evidence", {})
            },
            "localized_source_context": localized_code,
            "structural_context": {
                "function": function_context,
                "nesting": nesting_context,
                "ast_rule_detections": relevant_ast_rules,
                "cfg_summary": list(cfg_context.keys()) if cfg_context else [],
                "call_graph_calls": len(call_graph_context.get("calls", [])) if call_graph_context else 0,
                "dataflow_traces": dataflow_evidence,
                "retrieved_knowledge": retrieved_knowledge,
            }
        }

        user_content = json.dumps(payload, indent=2)
        response = self.llm_client.generate_structured(ROOT_CAUSE_SYSTEM_PROMPT, user_content)

        if response:
            # Enforce max 3 sentences constraint on root_cause
            rc_text = response.get("root_cause", "")
            sentences = [s.strip() for s in rc_text.split(".") if s.strip()]
            if len(sentences) > 3:
                response["root_cause"] = ". ".join(sentences[:3]) + "."

            # Enforce max 3 sentences constraint on fix
            fix_text = response.get("fix", "")
            fix_sentences = [s.strip() for s in fix_text.split(".") if s.strip()]
            if len(fix_sentences) > 3:
                response["fix"] = ". ".join(fix_sentences[:3]) + "."

            response["reasoning_source"] = "llm"
            return response

        return {
            "root_cause": f"Static analysis identified a code issue: {finding.get('issue')}.",
            "trigger_condition": "Triggers during execution of line.",
            "fix": "Please review the highlighted line and fix according to standard practices.",
            "patch": "",
            "issue_type": finding.get("issue_type", "code_smell"),
            "reasoning_source": "static_analysis"
        }

    def _extract_localized_code(self, aggregated_context: Dict[str, Any], line_no: int) -> str:
        """Extract bounded source code around the target line.

        Prefers extracting from full_code (target line ± context_lines) with line numbers,
        bounded by LLM_MAX_CONTEXT_LINES and LLM_MAX_CONTEXT_CHARS.
        Falls back to snippets or AST structure if full_code is not available.
        """
        context_lines_limit = getattr(self.settings, "LLM_MAX_CONTEXT_LINES", 50)
        max_chars = getattr(self.settings, "LLM_MAX_CONTEXT_CHARS", 4000)

        # 1. Primary: Extract from full_code if available
        full_code = aggregated_context.get("full_code", "")
        if full_code and isinstance(full_code, str):
            all_lines = full_code.splitlines()
            total_lines = len(all_lines)
            if total_lines > 0:
                start_idx = max(0, line_no - context_lines_limit - 1)
                end_idx = min(total_lines, line_no + context_lines_limit)
                
                formatted_lines = []
                for idx in range(start_idx, end_idx):
                    curr_line_no = idx + 1
                    marker = ">>>" if curr_line_no == line_no else "   "
                    formatted_lines.append(f"{marker} {curr_line_no:4d} | {all_lines[idx]}")
                
                result = "\n".join(formatted_lines)
                if len(result) > max_chars:
                    # Truncate symmetrically around target line
                    half = max_chars // 2
                    result = result[:half] + "\n... [context truncated] ...\n" + result[-half:]
                return result

        # 2. Secondary: Search code_context snippets with progressive window
        code_context = aggregated_context.get("code_context", [])
        if code_context and isinstance(code_context, list):
            for window in [5, 15, 30, 50]:
                for snippet in code_context:
                    snippet_code = snippet.get("code", "")
                    snippet_lines = snippet_code.splitlines()
                    start_line = snippet.get("start_line", 1)
                    end_line = start_line + len(snippet_lines)

                    if start_line - window <= line_no <= end_line + window:
                        formatted = []
                        for i, line_text in enumerate(snippet_lines):
                            curr_line = start_line + i
                            marker = ">>>" if curr_line == line_no else "   "
                            formatted.append(f"{marker} {curr_line:4d} | {line_text}")
                        return "\n".join(formatted)[:max_chars]

            # Fallback to first non-empty snippet
            for snippet in code_context:
                code = snippet.get("code", "")
                if code.strip():
                    return code[:max_chars]

        # 3. Tertiary: Fallback to AST structural context
        return self._fallback_source_context(aggregated_context, line_no)

    @staticmethod
    def _fallback_source_context(aggregated_context: Dict[str, Any], line_no: int) -> str:
        """Build a minimal structural source context when raw code is unavailable."""
        ast_struct = aggregated_context.get("ast_structural_metadata", {})
        if not isinstance(ast_struct, dict):
            return f"# Target line: {line_no} (source context unavailable)"

        context_parts = []

        # Include the enclosing function signature
        for func in ast_struct.get("functions", []):
            start = func.get("start_line", 0)
            end = func.get("end_line", 0)
            if start <= line_no <= end:
                name = func.get("name", "unknown")
                args = func.get("args", [])
                is_async = func.get("is_async", False)
                prefix = "async def" if is_async else "def"
                context_parts.append(f"# Enclosing function (lines {start}-{end}):")
                context_parts.append(f"{prefix} {name}({', '.join(args)}):")
                break

        # Include the enclosing class
        for cls in ast_struct.get("classes", []):
            start = cls.get("start_line", 0)
            end = cls.get("end_line", 0)
            if start <= line_no <= end:
                name = cls.get("name", "unknown")
                context_parts.insert(0, f"# Enclosing class (lines {start}-{end}):")
                context_parts.insert(1, f"class {name}:")
                break

        if context_parts:
            context_parts.append(f"# Target line: {line_no}")
            return "\n".join(context_parts)

        return f"# Target line: {line_no} (source context unavailable)"
