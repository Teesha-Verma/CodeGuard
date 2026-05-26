import pytest
from app.reasoning.review_generator import ReviewGenerator

def test_static_explanation_line_too_long():
    generator = ReviewGenerator("test_review")
    finding = {"line": 10, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "E501", "line too long (125 > 120)")
    assert "exceeds the maximum character length recommendation" in res["root_cause"]
    assert "Line 10 exceeds the maximum character length recommendation" in res["root_cause"]
    assert "Refactor the line by extracting sub-expressions" in res["fix"]
    assert "Line exceeds the configured maximum character length" in res["trigger_condition"]


def test_static_explanation_whitespace():
    generator = ReviewGenerator("test_review")
    finding = {"line": 15, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "W291", "trailing whitespace")
    assert "Inconsistent spacing, indentation, or trailing whitespace" in res["root_cause"]
    assert "Clean trailing whitespaces or adjust the indentation" in res["fix"]
    assert "Whitespace characters do not match standardized PEP-8" in res["trigger_condition"]


def test_static_explanation_docstrings():
    generator = ReviewGenerator("test_review")
    finding = {"line": 20, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "C0116", "Missing docstring")
    assert "Documenting public interfaces, classes, or modules provides vital context" in res["root_cause"]
    assert "Add a concise docstring summarizing the purpose" in res["fix"]
    assert "Public class, function, or module is missing" in res["trigger_condition"]


def test_static_explanation_nesting():
    generator = ReviewGenerator("test_review")
    finding = {"line": 25, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "EXCESSIVE_NESTING", "Deep block nesting")
    assert "Nesting depth on line 25 is high" in res["root_cause"]
    assert "Flatten nested structures by returning early" in res["fix"]
    assert "Block nesting depth exceeds recommended static limit" in res["trigger_condition"]


def test_static_explanation_shadowing():
    generator = ReviewGenerator("test_review")
    finding = {"line": 30, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "SHADOWING", "Shadowing local variable")
    assert "A local identifier on line 30 has the same name as a built-in" in res["root_cause"]
    assert "Rename the local variable to avoid namespace collisions" in res["fix"]
    assert "Local variable definition shadows a symbol from outer scopes" in res["trigger_condition"]
