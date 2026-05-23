"""Tests for MutationDetector — pattern-based iterable mutation detection."""
from app.static_analysis.mutation_detector import MutationDetector
import os

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_list_remove_during_iteration():
    code = (
        "def cleanup(items):\n"
        "    for item in items:\n"
        "        if item < 0:\n"
        "            items.remove(item)\n"
    )
    detector = MutationDetector()
    findings = detector.analyze(code)

    mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
    assert len(mutation_findings) == 1
    assert mutation_findings[0]["line"] == 4


def test_list_append_during_iteration():
    code = (
        "def grow(items):\n"
        "    for item in items:\n"
        "        items.append(item * 2)\n"
    )
    detector = MutationDetector()
    findings = detector.analyze(code)

    mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
    assert len(mutation_findings) == 1


def test_list_pop_during_iteration():
    code = (
        "def drain(items):\n"
        "    for item in items:\n"
        "        items.pop()\n"
    )
    detector = MutationDetector()
    findings = detector.analyze(code)

    mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
    assert len(mutation_findings) == 1


def test_shared_mutable_class_state():
    code = (
        "class Config:\n"
        "    options = []\n"
        "    data = {}\n"
    )
    detector = MutationDetector()
    findings = detector.analyze(code)

    class_findings = [f for f in findings if f["pattern"] == "shared_mutable_class_state"]
    assert len(class_findings) == 2


def test_safe_iteration_no_findings():
    code = (
        "def process(items):\n"
        "    results = []\n"
        "    for item in items:\n"
        "        results.append(item * 2)\n"
        "    return results\n"
    )
    detector = MutationDetector()
    findings = detector.analyze(code)

    # Appending to a different list (results) should not be flagged
    mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
    assert len(mutation_findings) == 0


def test_fixture_file_mutation():
    with open(os.path.join(FIXTURES_DIR, "sample_buggy.py"), "r") as f:
        code = f.read()

    detector = MutationDetector()
    findings = detector.analyze(code)

    # sample_buggy.py contains remove_while_iterating
    mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
    assert len(mutation_findings) >= 1


def test_syntax_error_returns_empty():
    detector = MutationDetector()
    findings = detector.analyze("def broken(:\n    pass")
    assert findings == []
