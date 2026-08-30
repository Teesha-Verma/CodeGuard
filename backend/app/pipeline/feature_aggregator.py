from typing import Dict, Any, List, Optional
from app.diff.diff_parser import DiffFile
from app.linters.base import LinterFinding


class FeatureAggregator:
    """Merges all deterministic static, structural, graph, and repository analysis signals into a unified context."""

    def aggregate(
        self,
        diff_file: DiffFile,
        context_snippets: List[Dict[str, Any]],
        ast_metadata: Dict[str, Any],
        complexity: Dict[str, Any],
        scope_data: List[Dict[str, Any]],
        control_flow: List[Dict[str, Any]],
        import_data: Dict[str, Any],
        mutation_data: List[Dict[str, Any]],
        linter_findings: List[LinterFinding],
        heuristic_findings: Optional[List[Dict[str, Any]]] = None,
        cfg_data: Optional[Dict[str, Any]] = None,
        call_graph_data: Optional[Dict[str, Any]] = None,
        dataflow_findings: Optional[List[Dict[str, Any]]] = None,
        repo_intelligence: Optional[Dict[str, Any]] = None,
        code_content: Optional[str] = None,
    ) -> Dict[str, Any]:

        linter_summary = []
        for finding in linter_findings:
            linter_summary.append({
                "line": finding.line,
                "rule": finding.rule_id,
                "message": finding.message,
                "severity": finding.severity if isinstance(finding.severity, str) else finding.severity.value,
                "tool": finding.tool_name
            })

        return {
            "file_path": diff_file.file_path,
            "changed_lines": diff_file.added_lines,
            "code_context": context_snippets,
            "full_code": code_content or "",
            # AST and static analysis signals
            "ast_structural_metadata": ast_metadata or {},
            "complexity_metrics": complexity or {},
            "scope_analysis": scope_data or [],
            "control_flow": control_flow or [],
            "import_analysis": import_data or {},
            "mutation_analysis": mutation_data or [],
            "linter_findings": linter_summary,
            "heuristic_findings": heuristic_findings or [],
            # Deep graph & flow intelligence
            "cfg_analysis": cfg_data or {},
            "call_graph_analysis": call_graph_data or {},
            "dataflow_analysis": dataflow_findings or [],
            "repository_intelligence": repo_intelligence or {},
        }
