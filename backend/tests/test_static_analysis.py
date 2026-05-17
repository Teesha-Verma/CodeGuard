from app.static_analysis.pattern_detector import PatternDetector

def test_mutable_default_detection():
    code = "def foo(x=[]):\n    pass"
    detector = PatternDetector()
    findings = detector.analyze(code)
    
    assert len(findings) == 1
    assert findings[0]["type"] == "mutable_default"
    assert findings[0]["line"] == 1
