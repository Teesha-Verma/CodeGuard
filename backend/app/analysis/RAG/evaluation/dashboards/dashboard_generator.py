"""
Dashboard Generator for RAG Evaluation.
"""

from typing import Any, Dict


class DashboardGenerator:
    """Generates data for RAG evaluation dashboards."""

    def generate_dashboard_summary(self, eval_summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a summary structure suitable for dashboard visualization.

        Args:
            eval_summary (Dict[str, Any]): Evaluation summary data.

        Returns:
            Dict[str, Any]: Dashboard-ready summary.
        """
        dashboard_data = {
            "title": "RAG Evaluation Dashboard",
            "widgets": []
        }
        
        for key, value in eval_summary.items():
            dashboard_data["widgets"].append({
                "type": "metric",
                "label": key.replace("_", " ").title(),
                "value": value
            })
            
        return dashboard_data
