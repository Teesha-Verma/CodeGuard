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
    
    # Mock settings.DEBUG to False to verify default lightweight mode
    from app.core.config import get_settings
    settings = get_settings()
    old_debug = settings.DEBUG
    settings.DEBUG = False
    
    try:
        # 1. Default (lightweight summary mode)
        report_default = orchestrator.process_file(diff_file, str(tmp_path), verbose_ast=False)
        assert report_default.ast_metadata is None
        assert report_default.ast_summary is not None
        assert report_default.ast_summary["function_count"] == 2
        assert report_default.ast_summary["class_count"] == 1
        assert report_default.ast_summary["dangerous_patterns"] == 0
    finally:
        settings.DEBUG = old_debug

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


def test_ast_payload_optimization_overrides(tmp_path):
    import os
    # Setup temporary file
    file_path = tmp_path / "hello.py"
    code = "def add(a, b): return a + b\n"
    file_path.write_text(code, encoding="utf-8")
    
    diff_file = DiffFile(
        file_path="hello.py",
        is_new=True,
        added_lines=[1]
    )
    
    orchestrator = PipelineOrchestrator(review_id="test-payload-overrides")
    
    # 1. Verification of developer mode override
    os.environ["DEVELOPER_MODE"] = "true"
    try:
        report = orchestrator.process_file(diff_file, str(tmp_path), verbose_ast=False)
        # Should be verbose even though verbose_ast is False because of DEVELOPER_MODE env override
        assert report.ast_metadata is not None
    finally:
        del os.environ["DEVELOPER_MODE"]

    # 2. Verification of debug mode override
    os.environ["DEBUG_MODE"] = "true"
    try:
        report = orchestrator.process_file(diff_file, str(tmp_path), verbose_ast=False)
        # Should be verbose even though verbose_ast is False because of DEBUG_MODE env override
        assert report.ast_metadata is not None
    finally:
        del os.environ["DEBUG_MODE"]

