import pytest
from app.reasoning.review_generator import ReviewGenerator

def test_static_explanation_line_too_long():
    generator = ReviewGenerator("test_review")
    finding = {"line": 10, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "E501", "line too long (125 > 120)")
    assert "exceeds the configured limit" in res["root_cause"]
    assert "This line on line 10 exceeds the configured limit (limit: 120 characters)" in res["root_cause"]
    assert "Consider splitting this line into logical segments" in res["fix"]
    assert "Occurs when a line exceeds the maximum recommended character limit." in res["trigger_condition"]

    res2 = generator._generate_static_explanation(finding, "E501", "line too long (125 > 120 characters)")
    assert "This line on line 10 exceeds the configured limit (limit: 120 characters)" in res2["root_cause"]


def test_static_explanation_whitespace():
    generator = ReviewGenerator("test_review")
    finding = {"line": 15, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "W291", "trailing whitespace")
    assert "Operator padding or trailing whitespace on line 15" in res["root_cause"]
    assert "Trim the trailing whitespace or adjust spacing" in res["fix"]
    assert "Flags trailing whitespace or inconsistent line spacing" in res["trigger_condition"]


def test_static_explanation_docstrings():
    generator = ReviewGenerator("test_review")
    finding = {"line": 20, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "C0116", "Missing docstring")
    assert "The public component on line 20 lacks inline documentation" in res["root_cause"]
    assert "Add a concise docstring summarizing the component" in res["fix"]
    assert "Flags public modules, classes, or functions" in res["trigger_condition"]


def test_static_explanation_nesting():
    generator = ReviewGenerator("test_review")
    finding = {"line": 25, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "EXCESSIVE_NESTING", "Deep block nesting")
    assert "The logic on line 25 has deep structural nesting" in res["root_cause"]
    assert "Refactor deep nesting by returning early with guard clauses" in res["fix"]
    assert "Triggered when nested block structures exceed" in res["trigger_condition"]


def test_static_explanation_shadowing():
    generator = ReviewGenerator("test_review")
    finding = {"line": 30, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "SHADOWING", "Shadowing local variable")
    assert "A variable definition on line 30 shadows a built-in" in res["root_cause"]
    assert "Rename this identifier to avoid name collisions" in res["fix"]
    assert "Occurs when a local scope declaration overrides a symbol" in res["trigger_condition"]
