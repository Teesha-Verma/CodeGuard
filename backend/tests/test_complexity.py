from app.static_analysis.complexity_analyzer import ComplexityAnalyzer
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_complexity_simple_function():
    code = "def add(a, b):\n    return a + b\n"
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(code)
    
    assert "functions" in result
    assert "maintainability_index" in result
    assert len(result["functions"]) == 1
    assert result["functions"][0]["name"] == "add"
    assert result["functions"][0]["complexity"] == 1  # No branches

def test_complexity_nested_branches():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(code)
    
    funcs = {f["name"]: f for f in result["functions"]}
    assert "deeply_nested" in funcs
    # deeply_nested has many if/else branches, complexity should be high
    assert funcs["deeply_nested"]["complexity"] > 5

def test_complexity_ranks():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze(code)
    
    for func in result["functions"]:
        assert "rank" in func
        assert func["rank"] in ("A", "B", "C", "D", "E", "F")

def test_complexity_syntax_error():
    analyzer = ComplexityAnalyzer()
    result = analyzer.analyze("def broken(:\n    pass")
    assert "error" in result
