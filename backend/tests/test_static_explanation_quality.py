import pytest
from app.reasoning.review_generator import ReviewGenerator

def test_static_explanation_line_too_long():
    generator = ReviewGenerator("test_review")
    finding = {"line": 10, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "E501", "line too long (125 > 120)")
    assert "stretches too far horizontally" in res["root_cause"]
    assert "Line 10 stretches too far horizontally" in res["root_cause"]
    assert "Consider breaking this line into multiple lines" in res["fix"]
    assert "This rule is triggered when a single line of code" in res["trigger_condition"]


def test_static_explanation_whitespace():
    generator = ReviewGenerator("test_review")
    finding = {"line": 15, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "W291", "trailing whitespace")
    assert "Line 15 contains minor spacing anomalies, such as extra whitespace" in res["root_cause"]
    assert "Remove the trailing whitespace or adjust spacing" in res["fix"]
    assert "Triggered by whitespace characters that deviate from standard" in res["trigger_condition"]


def test_static_explanation_docstrings():
    generator = ReviewGenerator("test_review")
    finding = {"line": 20, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "C0116", "Missing docstring")
    assert "The public interface, class, or function on line 20 is undocumented" in res["root_cause"]
    assert "Add a concise docstring that explains the component" in res["fix"]
    assert "This warning flags public declarations that are missing" in res["trigger_condition"]


def test_static_explanation_nesting():
    generator = ReviewGenerator("test_review")
    finding = {"line": 25, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "EXCESSIVE_NESTING", "Deep block nesting")
    assert "Line 25 has deeply nested logical blocks" in res["root_cause"]
    assert "Simplify the structure by returning early with guard clauses" in res["fix"]
    assert "This warning is raised when block nesting levels exceed" in res["trigger_condition"]


def test_static_explanation_shadowing():
    generator = ReviewGenerator("test_review")
    finding = {"line": 30, "issue_type": "style"}
    
    res = generator._generate_static_explanation(finding, "SHADOWING", "Shadowing local variable")
    assert "A variable definition on line 30 overrides or shadows" in res["root_cause"]
    assert "Rename the local variable to a more specific name" in res["fix"]
    assert "Occurs when a local variable shares a name with a symbol in an outer scope" in res["trigger_condition"]
