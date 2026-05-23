from app.static_analysis.pattern_detector import PatternDetector
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_mutable_default_detection():
    code = "def foo(x=[]):\n    pass"
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    assert len(findings) == 1
    assert findings[0]["type"] == "mutable_default"
    assert findings[0]["line"] == 1

def test_mutation_during_iteration():
    code = (
        "def cleanup(items):\n"
        "    for item in items:\n"
        "        if item < 0:\n"
        "            items.remove(item)\n"
    )
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    mutation_findings = [f for f in findings if f["type"] == "mutation_during_iteration"]
    assert len(mutation_findings) == 1

def test_dangerous_builtin_eval():
    code = "result = eval(user_input)"
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    assert len(findings) == 1
    assert findings[0]["type"] == "dangerous_builtin"
    assert "eval" in findings[0]["message"]

def test_dangerous_builtin_exec():
    code = "exec(some_code)"
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    assert len(findings) == 1
    assert findings[0]["type"] == "dangerous_builtin"

def test_clean_code_no_findings():
    code = "def add(a, b):\n    return a + b\n"
    detector = PatternDetector()
    findings = detector.analyze(code)
    assert findings == []

def test_full_fixture_file():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    types_found = {f["type"] for f in findings}
    assert "mutable_default" in types_found
    assert "mutation_during_iteration" in types_found
    assert "dangerous_builtin" in types_found
