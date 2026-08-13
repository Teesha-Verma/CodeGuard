"""Unit and integration tests for Final Phase: Evaluation, Benchmarking, Validation & Regression Testing in app.analysis.RAG.evaluation."""

import pytest
from app.analysis.RAG.evaluation.golden_dataset.golden_cases import GoldenDatasetManager, GoldenTestCase
from app.analysis.RAG.evaluation.retrieval.retrieval_evaluator import RetrievalEvaluator, RetrievalMetrics
from app.analysis.RAG.evaluation.review.review_evaluator import ReviewEvaluator, ReviewMetrics
from app.analysis.RAG.evaluation.comparisons.comparison_engine import ComparisonEngine, ComparisonResult
from app.analysis.RAG.evaluation.regression.regression_runner import RegressionRunner, RegressionResult
from app.analysis.RAG.evaluation.reports.report_generator import ReportGenerator
from app.analysis.RAG.evaluation.dashboards.dashboard_generator import DashboardGenerator
from app.analysis.RAG.evaluation.automation.evaluation_runner import EvaluationRunner


class TestGoldenDatasetAndRetrievalMetrics:
    """Test GoldenDatasetManager and RetrievalEvaluator."""

    def test_golden_dataset_manager(self):
        manager = GoldenDatasetManager()
        cases = manager.get_golden_dataset()
        assert len(cases) >= 5
        assert isinstance(cases[0], GoldenTestCase)

        sec_cases = manager.get_cases_by_category("security")
        assert len(sec_cases) >= 1

    def test_retrieval_evaluator(self):
        evaluator = RetrievalEvaluator()
        retrieved_docs = [
            {"source_path": "/kb/security/owasp_a03.md", "title": "OWASP A03 SQL Injection"},
            {"source_path": "/kb/python/fastapi_async.md", "title": "FastAPI Async Guide"},
        ]
        expected_sources = ["/kb/security/owasp_a03.md"]

        metrics: RetrievalMetrics = evaluator.evaluate_retrieval(retrieved_docs, expected_sources, k=2)
        assert isinstance(metrics, RetrievalMetrics)
        assert metrics.precision_at_k > 0.0
        assert metrics.recall_at_k == 1.0
        assert metrics.hit_rate == 1.0
        assert metrics.mrr > 0.0


class TestReviewEvaluatorAndComparisons:
    """Test ReviewEvaluator and ComparisonEngine."""

    def test_review_evaluator(self):
        evaluator = ReviewEvaluator()
        actual_review = {
            "review_summary": "Found critical SQL injection issue",
            "overall_severity": "critical",
            "findings": [
                {
                    "title": "SQL Injection vulnerability",
                    "severity": "critical",
                    "file_path": "app/auth.py",
                    "confidence": 0.95,
                }
            ],
            "confidence": 0.95,
        }
        ground_truth = {
            "ground_truth_findings": [
                {
                    "title": "SQL Injection vulnerability",
                    "severity": "critical",
                    "file_path": "app/auth.py",
                    "confidence": 0.95,
                }
            ],
            "ground_truth_severity": "critical",
            "ground_truth_confidence": 0.95,
        }

        metrics: ReviewMetrics = evaluator.evaluate_review(actual_review, ground_truth)
        assert isinstance(metrics, ReviewMetrics)
        assert metrics.precision > 0.0
        assert metrics.recall > 0.0
        assert metrics.f1_score > 0.0
        assert metrics.severity_accuracy == 1.0

    def test_comparison_engine(self):
        engine = ComparisonEngine()
        run_a = {"config_name": "Llama-3.3-70B", "f1_score": 0.85, "precision": 0.88, "recall": 0.82}
        run_b = {"config_name": "Qwen-3-32B", "f1_score": 0.78, "precision": 0.80, "recall": 0.76}

        res: ComparisonResult = engine.compare_pipeline_runs(run_a, run_b)
        assert isinstance(res, ComparisonResult)
        assert res.winner == "Llama-3.3-70B"
        assert res.improvement_percentage > 0.0


class TestRegressionReportsDashboardsAndAutomation:
    """Test RegressionRunner, ReportGenerator, DashboardGenerator, and EvaluationRunner."""

    def test_regression_runner(self):
        runner = RegressionRunner()
        manager = GoldenDatasetManager()
        cases = manager.get_golden_dataset()[:2]

        res: RegressionResult = runner.run_regression_suite(pipeline_service=None, golden_cases=cases)
        assert isinstance(res, RegressionResult)
        assert res.total_cases == 2
        assert res.pass_rate >= 0.0

    def test_report_and_dashboard_generators(self):
        report_gen = ReportGenerator()
        dash_gen = DashboardGenerator()

        metrics_summary = {
            "precision": 0.92,
            "recall": 0.88,
            "f1_score": 0.90,
            "mrr": 0.95,
            "total_evaluations": 10,
        }
        reg_result = RegressionResult(
            total_cases=10, passed_cases=10, failed_cases=0, regressions_detected=[], pass_rate=1.0
        )

        md_report = report_gen.generate_markdown_report(metrics_summary, reg_result)
        json_report = report_gen.generate_json_report(metrics_summary, reg_result)
        csv_report = report_gen.generate_csv_report(metrics_summary, reg_result)

        assert "CodeGuard V2" in md_report
        assert '"precision": 0.92' in json_report
        assert "Metric,Value" in csv_report

        dashboard = dash_gen.generate_dashboard_summary(metrics_summary)
        assert isinstance(dashboard, dict)
        assert "title" in dashboard or "widgets" in dashboard or "summary" in dashboard

    def test_evaluation_runner_full_suite(self):
        eval_runner = EvaluationRunner()
        res = eval_runner.run_full_evaluation_suite(service=None)
        assert isinstance(res, dict)
        assert "golden_cases_count" in res or "total_cases" in res or "status" in res
