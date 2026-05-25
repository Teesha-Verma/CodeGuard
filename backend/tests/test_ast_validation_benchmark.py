import pytest
import ast
from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.heuristic_engine import HeuristicEngine
from app.static_analysis.mutation_detector import MutationDetector
from app.static_analysis.pattern_detector import PatternDetector
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.import_analyzer import ImportAnalyzer

# ==========================================
# 1. MUTATION DURING ITERATION
# ==========================================

def test_mutation_during_iteration_dangerous():
    dangerous_code = """
def mutate_loop(items):
    for item in items:
        items.remove(item)
"""
    # 1. Test MutationDetector
    mut_detector = MutationDetector()
    findings = mut_detector.analyze(dangerous_code)
    assert len(findings) >= 1
    assert any("list mutation during iteration" in f["pattern"] for f in findings)
    
    # 2. Test PatternDetector
    pat_detector = PatternDetector()
    findings_pat = pat_detector.analyze(dangerous_code)
    assert len(findings_pat) >= 1
    assert any("mutation_during_iteration" in f["type"] for f in findings_pat)

    # 3. Test HeuristicEngine
    heuristic_engine = HeuristicEngine()
    findings_heur = heuristic_engine.analyze(dangerous_code)
    assert len(findings_heur) >= 1
    assert any("mutation_during_iteration" in f["rule_name"] for f in findings_heur)

    # 4. Test PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    ast_findings = res["ast_rules_findings"]
    assert any(f["rule_name"] == "mutation_during_iteration" for f in ast_findings)


def test_mutation_during_iteration_safe():
    safe_code = """
def safe_mutate_loop(items):
    for item in list(items):
        items.remove(item)
"""
    # Verify no mutation findings are triggered when iterating over a copy
    mut_detector = MutationDetector()
    assert mut_detector.analyze(safe_code) == []

    pat_detector = PatternDetector()
    assert pat_detector.analyze(safe_code) == []

    heuristic_engine = HeuristicEngine()
    # Broad rule or specific rule shouldn't trigger mutation during iteration here
    mut_findings = [f for f in heuristic_engine.analyze(safe_code) if f["rule_name"] == "mutation_during_iteration"]
    assert mut_findings == []

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    ast_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "mutation_during_iteration"]
    assert ast_findings == []


# ==========================================
# 2. SUBPROCESS EXECUTION
# ==========================================

def test_subprocess_dangerous():
    dangerous_code = """
import subprocess
def run_cmd(user_val):
    subprocess.run(user_val, shell=True)
"""
    # 1. Test ImportAnalyzer
    imp_analyzer = ImportAnalyzer()
    res_imp = imp_analyzer.analyze(dangerous_code)
    assert len(res_imp["dangerous_imports"]) >= 1
    assert any("subprocess" in f["module"] for f in res_imp["dangerous_imports"])

    # 2. Test PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    sub_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "unsafe_subprocess"]
    assert len(sub_findings) >= 1
    assert any("shell=True" in f["message"] for f in sub_findings)


def test_subprocess_safe():
    safe_code = """
import subprocess
def run_safe_cmd():
    subprocess.run(["ls", "-la"])
"""
    # 1. Import analyzer flags "subprocess" import itself (expected, it's a dangerous import)
    # 2. Verify PythonASTParser does NOT flag it as an unsafe shell/dynamic subprocess call
    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    sub_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "unsafe_subprocess"]
    # Should be 0 since shell=False and command is static list of constants
    assert len(sub_findings) == 0


# ==========================================
# 3. PICKLE DESERIALIZATION
# ==========================================

def test_pickle_dangerous():
    dangerous_code = """
import pickle
def deserialize(data):
    return pickle.loads(data)
"""
    # 1. ImportAnalyzer
    imp_analyzer = ImportAnalyzer()
    res_imp = imp_analyzer.analyze(dangerous_code)
    assert any("pickle" in f["module"] for f in res_imp["dangerous_imports"])

    # 2. PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    pickle_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "unsafe_pickle"]
    assert len(pickle_findings) >= 1
    assert "pickle.loads" in pickle_findings[0]["message"]


def test_pickle_safe():
    safe_code = """
import json
def deserialize(data):
    return json.loads(data)
"""
    # JSON is completely safe, no pickle/marshal/etc imports or calls
    imp_analyzer = ImportAnalyzer()
    res_imp = imp_analyzer.analyze(safe_code)
    assert len(res_imp["dangerous_imports"]) == 0

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    pickle_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "unsafe_pickle"]
    assert len(pickle_findings) == 0


# ==========================================
# 4. VARIABLE SHADOWING
# ==========================================

def test_variable_shadowing_dangerous():
    dangerous_code = """
x = 10
def shadow():
    list = [1, 2, 3]
    x = 5
    return list, x
"""
    # 1. ScopeTracker
    scope_tracker = ScopeTracker()
    findings = scope_tracker.analyze(dangerous_code)
    assert len(findings) >= 1
    assert any(f["pattern"] == "variable_shadowing" and "x" in f["message"] for f in findings)

    # 2. PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    shadow_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "variable_shadowing"]
    assert len(shadow_findings) >= 2
    assert any("list" in f["message"] for f in shadow_findings)
    assert any("x" in f["message"] for f in shadow_findings)


def test_variable_shadowing_safe():
    safe_code = """
x = 10
def safe_variables():
    global x
    x = 5
    my_list = [1, 2, 3]
    return my_list, x
"""
    scope_tracker = ScopeTracker()
    findings = scope_tracker.analyze(safe_code)
    # Declaring 'global x' does not shadow the global x (it mutates it cleanly), and my_list does not shadow anything
    shadowing_findings = [f for f in findings if f["pattern"] == "variable_shadowing"]
    assert len(shadowing_findings) == 0

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    shadow_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "variable_shadowing"]
    assert len(shadow_findings) == 0


# ==========================================
# 5. DYNAMIC EXECUTION
# ==========================================

def test_dynamic_execution_dangerous():
    dangerous_code = """
def run_dynamic(code):
    eval(code)
    exec(code)
"""
    # 1. PatternDetector
    pat_detector = PatternDetector()
    findings_pat = pat_detector.analyze(dangerous_code)
    assert len(findings_pat) >= 2
    assert any(f["type"] == "dangerous_builtin" and "eval" in f["message"] for f in findings_pat)
    assert any(f["type"] == "dangerous_builtin" and "exec" in f["message"] for f in findings_pat)

    # 2. HeuristicEngine
    heuristic_engine = HeuristicEngine()
    findings_heur = heuristic_engine.analyze(dangerous_code)
    assert any(f["rule_name"] == "dangerous_builtin" and "eval" in f["message"] for f in findings_heur)
    assert any(f["rule_name"] == "dangerous_builtin" and "exec" in f["message"] for f in findings_heur)

    # 3. PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    eval_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "eval_detection"]
    exec_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "exec_detection"]
    assert len(eval_findings) >= 1
    assert len(exec_findings) >= 1


def test_dynamic_execution_safe():
    safe_code = """
def run_static():
    x = 10
    y = 20
    return x + y
"""
    pat_detector = PatternDetector()
    assert pat_detector.analyze(safe_code) == []

    heuristic_engine = HeuristicEngine()
    assert [f for f in heuristic_engine.analyze(safe_code) if f["rule_name"] == "dangerous_builtin"] == []

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    assert [f for f in res["ast_rules_findings"] if f["rule_name"] in ("eval_detection", "exec_detection")] == []


# ==========================================
# 6. RECURSION RISK
# ==========================================

def test_recursion_risk_dangerous():
    dangerous_code = """
def infinite_rec(n):
    return infinite_rec(n - 1)
"""
    # 1. HeuristicEngine
    heuristic_engine = HeuristicEngine()
    findings_heur = heuristic_engine.analyze(dangerous_code)
    assert any(f["rule_name"] == "recursion_risk" for f in findings_heur)

    # 2. PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    rec_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "recursion_risk"]
    assert len(rec_findings) >= 1


def test_recursion_risk_safe():
    safe_code = """
def safe_rec(n):
    if n <= 0:
        return 0
    return safe_rec(n - 1)
"""
    heuristic_engine = HeuristicEngine()
    findings_heur = [f for f in heuristic_engine.analyze(safe_code) if f["rule_name"] == "recursion_risk"]
    # Has a conditional (ast.If), so recursion_risk should not trigger
    assert len(findings_heur) == 0

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    rec_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "recursion_risk"]
    assert len(rec_findings) == 0


# ==========================================
# 7. ASYNC MISUSE & UNAWAITED CALLS
# ==========================================

def test_async_misuse_dangerous():
    dangerous_code = """
import time
import requests

async def fetch_data():
    time.sleep(1)
    requests.get("https://example.com")
"""
    # 1. HeuristicEngine
    heuristic_engine = HeuristicEngine()
    findings_heur = heuristic_engine.analyze(dangerous_code)
    assert any(f["rule_name"] == "async_misuse" and "time.sleep" in f["message"] for f in findings_heur)
    assert any(f["rule_name"] == "async_misuse" and "requests.get" in f["message"] for f in findings_heur)

    # 2. PythonASTParser
    parser = PythonASTParser()
    res = parser.parse(dangerous_code, [])
    async_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "async_misuse"]
    assert len(async_findings) >= 2


def test_async_misuse_safe():
    safe_code = """
import asyncio
async def safe_fetch():
    await asyncio.sleep(1)
"""
    heuristic_engine = HeuristicEngine()
    findings_heur = [f for f in heuristic_engine.analyze(safe_code) if f["rule_name"] == "async_misuse"]
    assert len(findings_heur) == 0

    parser = PythonASTParser()
    res = parser.parse(safe_code, [])
    async_findings = [f for f in res["ast_rules_findings"] if f["rule_name"] == "async_misuse"]
    assert len(async_findings) == 0
