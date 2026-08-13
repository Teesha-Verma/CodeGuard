"""
Report Generator for RAG Evaluation.
"""

import json
import csv
from typing import Any, Dict
import io


class ReportGenerator:
    """Generates evaluation reports in various formats."""

    def generate_markdown_report(self, metrics: Dict[str, Any], regression: Any) -> str:
        """
        Generates a markdown report.

        Args:
            metrics (Dict[str, Any]): Evaluation metrics.
            regression (Any): Regression results.

        Returns:
            str: Markdown formatted report.
        """
        lines = []
        lines.append("# CodeGuard V2 RAG Evaluation Report")
        lines.append("")
        lines.append("## Metrics")
        for k, v in metrics.items():
            lines.append(f"- **{k}**: {v}")
        
        lines.append("")
        lines.append("## Regression Results")
        if hasattr(regression, "model_dump"):
            reg_dict = regression.model_dump()
            for k, v in reg_dict.items():
                lines.append(f"- **{k}**: {v}")
        
        return "\n".join(lines)

    def generate_json_report(self, metrics: Dict[str, Any], regression: Any) -> str:
        """
        Generates a JSON report.

        Args:
            metrics (Dict[str, Any]): Evaluation metrics.
            regression (Any): Regression results.

        Returns:
            str: JSON formatted report.
        """
        data = {
            "metrics": metrics,
            "regression": regression.model_dump() if hasattr(regression, "model_dump") else regression
        }
        return json.dumps(data, indent=2)

    def generate_csv_report(self, metrics: Dict[str, Any], regression: Any) -> str:
        """
        Generates a CSV report.

        Args:
            metrics (Dict[str, Any]): Evaluation metrics.
            regression (Any): Regression results.

        Returns:
            str: CSV formatted report.
        """
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Category", "Metric", "Value"])
        for k, v in metrics.items():
            writer.writerow(["Metrics", k, str(v)])
            
        if hasattr(regression, "model_dump"):
            reg_dict = regression.model_dump()
            for k, v in reg_dict.items():
                writer.writerow(["Regression", k, str(v)])
                
        return output.getvalue()
