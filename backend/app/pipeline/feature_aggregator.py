from typing import Dict, Any, List
from app.diff.diff_parser import DiffFile
from app.linters.base import LinterFinding

class FeatureAggregator:
    """Merges all static analysis signals into a unified context for the LLM."""
    
    def aggregate(
        self, 
        diff_file: DiffFile, 
        context_snippets: List[Dict[str, Any]], 
        ast_metadata: List[Dict[str, Any]],
        complexity: Dict[str, Any],
        scope_data: List[Dict[str, Any]],
        control_flow: List[Dict[str, Any]],
        dependencies: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]],
        linter_findings: List[LinterFinding]
    ) -> Dict[str, Any]:
        
        linter_summary = []
        for finding in linter_findings:
            linter_summary.append({
                "line": finding.line,
                "rule": finding.rule_id,
                "message": finding.message,
                "severity": finding.severity.value,
                "tool": finding.tool_name
            })
            
        return {
            "file_path": diff_file.file_path,
            "changed_lines": diff_file.added_lines,
            "code_context": context_snippets,
            "ast_structural_metadata": ast_metadata,
            "complexity_metrics": complexity,
            "scope_analysis": scope_data,
            "control_flow": control_flow,
            "dependencies": dependencies,
            "dangerous_patterns": patterns,
            "linter_findings": linter_summary
        }
