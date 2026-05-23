"""Tests for grounding integrity — safe code must produce zero false positives from deterministic analysis."""
from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.mutation_detector import MutationDetector
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.pattern_detector import PatternDetector
from app.static_analysis.import_analyzer import ImportAnalyzer


# --------------------------------------------------------------------------- #
#                      Safe Code Snippets (no issues expected)                 #
# --------------------------------------------------------------------------- #

SAFE_SIMPLE = """\
def add(a, b):
    return a + b
"""

SAFE_LOOP = """\
def double_items(items):
    results = []
    for item in items:
        results.append(item * 2)
    return results
"""

SAFE_CLASS = """\
class Calculator:
    def __init__(self, initial=0):
        self.value = initial

    def add(self, x):
        self.value += x
        return self.value
"""

SAFE_IMPORT = """\
import json
import math
from typing import List, Dict
"""

SAFE_SCOPE = """\
def compute(x, y):
    result = x + y
    return result
"""


# --------------------------------------------------------------------------- #
#                             Grounding Tests                                  #
# --------------------------------------------------------------------------- #

class TestGroundingNoFalsePositives:
    """Ensures deterministic analyzers produce zero findings on clean code."""

    def test_safe_simple_no_ast_issues(self):
        parser = PythonASTParser()
        result = parser.parse(SAFE_SIMPLE, [1, 2])
        assert result["async_issues"] == []

    def test_safe_simple_no_mutations(self):
        detector = MutationDetector()
        assert detector.analyze(SAFE_SIMPLE) == []

    def test_safe_simple_no_scope_issues(self):
        tracker = ScopeTracker()
        assert tracker.analyze(SAFE_SIMPLE) == []

    def test_safe_simple_no_pattern_issues(self):
        detector = PatternDetector()
        assert detector.analyze(SAFE_SIMPLE) == []

    def test_safe_loop_no_mutations(self):
        detector = MutationDetector()
        findings = detector.analyze(SAFE_LOOP)
        mutation_findings = [f for f in findings if f["pattern"] == "list mutation during iteration"]
        assert len(mutation_findings) == 0

    def test_safe_loop_no_pattern_issues(self):
        detector = PatternDetector()
        findings = detector.analyze(SAFE_LOOP)
        assert len(findings) == 0

    def test_safe_class_no_shared_state(self):
        detector = MutationDetector()
        findings = detector.analyze(SAFE_CLASS)
        class_findings = [f for f in findings if f["pattern"] == "shared_mutable_class_state"]
        assert len(class_findings) == 0

    def test_safe_import_no_dangerous(self):
        analyzer = ImportAnalyzer()
        # Clean safe imports that should never trigger dangerous imports
        safe_code = """
import sys
import typing
import pathlib
import json
import collections
import os
from collections import defaultdict
"""
        result = analyzer.analyze(safe_code)
        assert result["dangerous_imports"] == []

    def test_safe_scope_no_shadowing(self):
        tracker = ScopeTracker()
        assert tracker.analyze(SAFE_SCOPE) == []


class TestGroundingKnownBugs:
    """Ensures deterministic analyzers correctly flag known-bad patterns."""

    def test_mutable_default_detected(self):
        code = "def foo(x=[]):\n    x.append(1)\n    return x\n"
        detector = PatternDetector()
        findings = detector.analyze(code)
        assert any(f["type"] == "mutable_default" for f in findings)

    def test_iteration_mutation_detected(self):
        code = (
            "def cleanup(items):\n"
            "    for item in items:\n"
            "        if item < 0:\n"
            "            items.remove(item)\n"
        )
        detector = MutationDetector()
        findings = detector.analyze(code)
        assert any(f["pattern"] == "list mutation during iteration" for f in findings)

    def test_dangerous_eval_detected(self):
        code = "result = eval(user_input)\n"
        detector = PatternDetector()
        findings = detector.analyze(code)
        assert any(f["type"] == "dangerous_builtin" for f in findings)

    def test_global_modification_detected(self):
        code = "config = {}\ndef update():\n    global config\n    config = {'new': True}\n"
        tracker = ScopeTracker()
        findings = tracker.analyze(code)
        assert any(f["pattern"] == "global_modification" for f in findings)

    def test_dangerous_import_detected(self):
        code = """
import subprocess
import pickle
import marshal
import ctypes
from os import system
"""
        analyzer = ImportAnalyzer()
        result = analyzer.analyze(code)
        assert len(result["dangerous_imports"]) == 5
        modules = [x["module"] for x in result["dangerous_imports"]]
        assert "subprocess" in modules
        assert "pickle" in modules
        assert "marshal" in modules
        assert "ctypes" in modules
        assert "os.system" in modules

    def test_shared_mutable_class_state_detected(self):
        code = "class BadConfig:\n    items = []\n"
        detector = MutationDetector()
        findings = detector.analyze(code)
        assert any(f["pattern"] == "shared_mutable_class_state" for f in findings)
