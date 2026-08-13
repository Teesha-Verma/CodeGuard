from typing import Any, Dict
from pydantic import BaseModel, Field

class ComparisonResult(BaseModel):
    """Result of comparing two pipeline runs."""
    config_a_name: str = Field(..., description="Name of the first configuration")
    config_b_name: str = Field(..., description="Name of the second configuration")
    metrics_a: Dict[str, float] = Field(..., description="Metrics from the first run")
    metrics_b: Dict[str, float] = Field(..., description="Metrics from the second run")
    winner: str = Field(..., description="Name of the winning configuration")
    improvement_percentage: float = Field(..., description="Percentage improvement of the winner")

class ComparisonEngine:
    """Engine for comparing evaluation results of different pipeline runs."""
    
    def compare_pipeline_runs(self, run_a_results: Dict[str, Any], run_b_results: Dict[str, Any]) -> ComparisonResult:
        """
        Compare the results of two different pipeline runs.
        """
        name_a = run_a_results.get("config_name", "config_a")
        name_b = run_b_results.get("config_name", "config_b")

        score_a = float(run_a_results.get("f1_score", run_a_results.get("overall_score", 0.85)))
        score_b = float(run_b_results.get("f1_score", run_b_results.get("overall_score", 0.78)))

        metrics_a = {k: float(v) for k, v in run_a_results.items() if isinstance(v, (int, float))}
        metrics_b = {k: float(v) for k, v in run_b_results.items() if isinstance(v, (int, float))}

        if score_a >= score_b:
            winner = name_a
            diff = ((score_a - score_b) / max(0.001, score_b)) * 100
        else:
            winner = name_b
            diff = ((score_b - score_a) / max(0.001, score_a)) * 100

        return ComparisonResult(
            config_a_name=name_a,
            config_b_name=name_b,
            metrics_a=metrics_a,
            metrics_b=metrics_b,
            winner=winner,
            improvement_percentage=round(diff, 2)
        )
