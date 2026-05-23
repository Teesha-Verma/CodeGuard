from app.static_analysis.ast_parser import PythonASTParser
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

def test_ast_parser_extracts_functions():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    parser = PythonASTParser()
    # Pass all lines as changed to get all functions
    all_lines = list(range(1, code.count("\n") + 2))
    result = parser.parse(code, all_lines)
    
    # V1: parse returns a dict with "functions", "classes", etc.
    assert "functions" in result
    assert "classes" in result
    assert "control_structures" in result
    assert "async_issues" in result
    
    func_names = [item["name"] for item in result["functions"]]
    assert "append_to_list" in func_names
    assert "remove_while_iterating" in func_names
    assert "deeply_nested" in func_names

def test_ast_parser_detects_docstrings():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    parser = PythonASTParser()
    all_lines = list(range(1, code.count("\n") + 2))
    result = parser.parse(code, all_lines)
    
    for item in result["functions"]:
        assert "has_docstring" in item
        assert item["has_docstring"] is True  # All sample functions have docstrings

def test_ast_parser_handles_syntax_error():
    parser = PythonASTParser()
    result = parser.parse("def foo(:\n    pass", [1])
    # V1: returns a dict with empty lists on syntax error
    assert result.get("functions") == []
    assert result.get("classes") == []
    assert result.get("control_structures") == []
    assert result.get("async_issues") == []

def test_ast_parser_filters_by_changed_lines():
    code = "def first():\n    pass\n\ndef second():\n    pass\n"
    parser = PythonASTParser()
    # Only line 1-2 changed, should mark first as changed
    result = parser.parse(code, [1, 2])
    
    changed_funcs = [f for f in result["functions"] if f["is_changed"]]
    assert len(changed_funcs) == 1
    assert changed_funcs[0]["name"] == "first"

def test_ast_parser_detects_recursion():
    code = "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n"
    parser = PythonASTParser()
    result = parser.parse(code, [1, 2, 3, 4])
    
    assert len(result["functions"]) == 1
    assert result["functions"][0]["is_recursive"] is True

def test_ast_parser_detects_async_missing_await():
    code = "import asyncio\nasync def do_work():\n    return 42\n"
    parser = PythonASTParser()
    result = parser.parse(code, [1, 2, 3])
    
    assert len(result["async_issues"]) >= 1
    issue_types = [i["type"] for i in result["async_issues"]]
    assert "async_missing_await" in issue_types

def test_ast_parser_extracts_classes():
    code = "class MyClass(Base):\n    def method(self):\n        pass\n"
    parser = PythonASTParser()
    result = parser.parse(code, [1, 2, 3])
    
    assert len(result["classes"]) == 1
    assert result["classes"][0]["name"] == "MyClass"
    assert "Base" in result["classes"][0]["bases"]
    assert "method" in result["classes"][0]["methods"]
