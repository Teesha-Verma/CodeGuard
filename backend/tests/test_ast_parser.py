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
    
    func_names = [item["name"] for item in result]
    assert "append_to_list" in func_names
    assert "remove_while_iterating" in func_names
    assert "deeply_nested" in func_names

def test_ast_parser_detects_docstrings():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()
    
    parser = PythonASTParser()
    all_lines = list(range(1, code.count("\n") + 2))
    result = parser.parse(code, all_lines)
    
    for item in result:
        if item["type"] in ("FunctionDef", "AsyncFunctionDef"):
            assert "has_docstring" in item
            assert item["has_docstring"] is True  # All sample functions have docstrings

def test_ast_parser_handles_syntax_error():
    parser = PythonASTParser()
    result = parser.parse("def foo(:\n    pass", [1])
    assert result == []

def test_ast_parser_filters_by_changed_lines():
    code = "def first():\n    pass\n\ndef second():\n    pass\n"
    parser = PythonASTParser()
    # Only line 1-2 changed, should only pick up `first`
    result = parser.parse(code, [1, 2])
    
    assert len(result) == 1
    assert result[0]["name"] == "first"
