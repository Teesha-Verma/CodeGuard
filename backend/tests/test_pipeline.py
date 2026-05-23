from app.static_analysis.control_flow import ControlFlowAnalyzer
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.dependency_analyzer import DependencyAnalyzer
from app.evaluation.metrics import MetricsCalculator
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# --- Control Flow ---

def test_bare_except_detection():
    code = "try:\n    x = 1/0\nexcept:\n    pass\n"
    analyzer = ControlFlowAnalyzer()
    findings = analyzer.analyze(code)
    
    assert len(findings) == 1
    assert findings[0]["type"] == "bare_except"

def test_specific_except_no_finding():
    code = "try:\n    x = 1/0\nexcept ZeroDivisionError:\n    pass\n"
    analyzer = ControlFlowAnalyzer()
    findings = analyzer.analyze(code)
    assert findings == []

# --- Scope Tracker (V1 API: returns findings with pattern/message) ---

def test_scope_tracker_global_modification():
    code = "x = 10\ndef change_x():\n    global x\n    x = 20\n"
    tracker = ScopeTracker()
    findings = tracker.analyze(code)
    
    assert len(findings) >= 1
    patterns = [f["pattern"] for f in findings]
    assert "global_modification" in patterns

def test_scope_tracker_variable_shadowing():
    code = "x = 10\ndef foo():\n    x = 20\n    return x\n"
    tracker = ScopeTracker()
    findings = tracker.analyze(code)
    
    assert len(findings) >= 1
    patterns = [f["pattern"] for f in findings]
    assert "variable_shadowing" in patterns

def test_scope_tracker_no_issue_on_clean_code():
    code = "def add(a, b):\n    return a + b\n"
    tracker = ScopeTracker()
    findings = tracker.analyze(code)
    assert findings == []

# --- Dependency Analyzer ---

def test_import_detection():
    code = "import os\nfrom pathlib import Path\nimport json\n"
    analyzer = DependencyAnalyzer()
    imports = analyzer.analyze(code)
    
    assert len(imports) == 3
    modules = [i["module"] for i in imports]
    assert "os" in modules
    assert "pathlib" in modules

# --- Metrics Calculator ---

def test_summary_stats_empty():
    stats = MetricsCalculator.compute_summary_stats([])
    assert stats["total_issues"] == 0
    assert stats["avg_confidence"] == 0.0

def test_summary_stats_with_issues():
    issues = [
        {"severity": "high", "source": "llm", "confidence": 0.9},
        {"severity": "medium", "source": "linter", "confidence": 0.7},
        {"severity": "critical", "source": "llm", "confidence": 0.95},
    ]
    stats = MetricsCalculator.compute_summary_stats(issues)
    
    assert stats["total_issues"] == 3
    assert stats["by_severity"]["high"] == 1
    assert stats["by_severity"]["critical"] == 1
    assert stats["by_source"]["llm"] == 2
    assert stats["by_source"]["linter"] == 1
    assert stats["avg_confidence"] == round((0.9 + 0.7 + 0.95) / 3, 2)
