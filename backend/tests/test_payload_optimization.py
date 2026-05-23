import os
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile

def test_ast_payload_optimization(tmp_path):
    # Setup temporary file
    file_path = tmp_path / "hello.py"
    code = """
class SafeClass:
    def greet(self):
        return "hello"

def add(a, b):
    return a + b
"""
    file_path.write_text(code, encoding="utf-8")
    
    diff_file = DiffFile(
        file_path="hello.py",
        is_new=True,
        added_lines=[1, 2, 3, 4, 5, 6, 7]
    )
    
    orchestrator = PipelineOrchestrator(review_id="test-payload")
    
    # 1. Default (lightweight summary mode)
    report_default = orchestrator.process_file(diff_file, str(tmp_path), verbose_ast=False)
    assert report_default.ast_metadata is None
    assert report_default.ast_summary is not None
    assert report_default.ast_summary["function_count"] == 2
    assert report_default.ast_summary["class_count"] == 1
    assert report_default.ast_summary["dangerous_patterns"] == 0

    # 2. Verbose mode
    report_verbose = orchestrator.process_file(diff_file, str(tmp_path), verbose_ast=True)
    assert report_verbose.ast_metadata is not None
    assert "functions" in report_verbose.ast_metadata
    assert "classes" in report_verbose.ast_metadata
    assert "complexity" in report_verbose.ast_metadata
    assert "dangerous_calls" in report_verbose.ast_metadata
    assert len(report_verbose.ast_metadata["functions"]) == 2
    assert len(report_verbose.ast_metadata["classes"]) == 1
    assert report_verbose.ast_summary is not None
