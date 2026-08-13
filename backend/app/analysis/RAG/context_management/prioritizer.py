"""
Context prioritization module.
"""
from typing import Any, Dict, List


class ContextPrioritizer:
    """
    Prioritizes analysis findings and retrieved knowledge based on a strict 9-tier priority hierarchy:
    1. Critical Security Issues
    2. High Confidence Findings
    3. Framework-Specific Guidance
    4. Official Standards (OWASP / CWE / CERT)
    5. Repository Rules
    6. Architecture Guidance
    7. Historical Reviews
    8. Examples
    9. General Best Practices
    """

    def prioritize(
        self,
        retrieved_context: Any = None,
        repo_context: Any = None,
        analysis_findings: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrates prioritization of findings, retrieved context, and repo rules.
        """
        sorted_findings = self.prioritize_findings(analysis_findings or [])
        results_list = []
        if hasattr(retrieved_context, "retrieved_results"):
            results_list = retrieved_context.retrieved_results
        elif isinstance(retrieved_context, list):
            results_list = retrieved_context
        sorted_knowledge = self.prioritize_knowledge(results_list)

        return {
            "findings": sorted_findings,
            "knowledge": sorted_knowledge,
            "repo_context": repo_context or {},
        }

    def prioritize_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritizes a list of analysis findings based on severity and confidence.

        Args:
            findings: List of analysis findings.

        Returns:
            List of prioritized findings.
        """
        def get_priority(finding: Dict[str, Any]) -> int:
            severity = str(finding.get("severity", "")).lower()
            confidence = str(finding.get("confidence", "")).lower()
            
            if severity in ("critical", "high"):
                return 1  # Critical Security Issues
            elif confidence == "high":
                return 2  # High Confidence Findings
            else:
                return 10 # Lowest priority for findings

        return sorted(findings, key=get_priority)

    def prioritize_knowledge(self, retrieved_results: List[Any]) -> List[Any]:
        """
        Prioritizes retrieved knowledge based on the defined hierarchy.
        
        Args:
            retrieved_results: List of retrieved knowledge items.

        Returns:
            List of prioritized knowledge items.
        """
        def get_priority(item: Any) -> int:
            if isinstance(item, dict):
                category = str(item.get("category", "")).lower()
                source = str(item.get("source", "")).lower()
                
                if "framework" in category:
                    return 3
                elif any(std in source for std in ("owasp", "cwe", "cert")):
                    return 4
                elif "rule" in category or "repo" in category:
                    return 5
                elif "architecture" in category:
                    return 6
                elif "history" in category or "review" in category:
                    return 7
                elif "example" in category:
                    return 8
                else:
                    return 9
            return 9 # Default to General Best Practices

        return sorted(retrieved_results, key=get_priority)
