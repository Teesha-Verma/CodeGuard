import pytest
from app.static_analysis.ast_parser import PythonASTParser

def test_ast_eval_and_exec_detection():
    code = """
def run_dynamic(user_input):
    eval(user_input)
    exec("print('hello')")
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    rules = [f["rule_name"] for f in findings]
    assert "eval_detection" in rules
    assert "exec_detection" in rules
    
    eval_f = [f for f in findings if f["rule_name"] == "eval_detection"][0]
    exec_f = [f for f in findings if f["rule_name"] == "exec_detection"][0]
    
    assert "eval" in eval_f["message"]
    assert "exec" in exec_f["message"]

def test_ast_unsafe_subprocess_detection():
    code = """
import subprocess
import os

def call_shell(cmd):
    subprocess.run(cmd, shell=True)
    subprocess.Popen("ping " + cmd)
    os.system(cmd)
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    sub_findings = [f for f in findings if f["rule_name"] == "unsafe_subprocess"]
    assert len(sub_findings) == 3
    
    messages = [f["message"] for f in sub_findings]
    assert any("shell=True" in m for m in messages)
    assert any("dynamic command" in m for m in messages)
    assert any("os.system" in m for m in messages)

def test_ast_unsafe_pickle_detection():
    code = """
import pickle

def load_data(raw_bytes):
    return pickle.loads(raw_bytes)
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    pickle_findings = [f for f in findings if f["rule_name"] == "unsafe_pickle"]
    assert len(pickle_findings) == 1
    assert "pickle.loads" in pickle_findings[0]["message"]

def test_ast_nested_loops_detection():
    code = """
def process_matrix(matrix):
    for row in matrix:
        for val in row:
            for item in val:
                print(item)
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    nested_findings = [f for f in findings if f["rule_name"] == "nested_loop"]
    assert len(nested_findings) >= 1
    assert "deeper than 2 layers" in nested_findings[0]["message"]

def test_ast_variable_shadowing_detection():
    code = """
x = 10

def shadow_test(id):
    x = 5
    list = [1, 2]
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    shadow_findings = [f for f in findings if f["rule_name"] == "variable_shadowing"]
    assert len(shadow_findings) >= 3
    
    shadowed_vars = [f["message"] for f in shadow_findings]
    assert any("id" in m for m in shadowed_vars)
    assert any("x" in m for m in shadowed_vars)
    assert any("list" in m for m in shadowed_vars)

def test_ast_mutation_during_iteration_detection():
    code = """
def mutate_loop(items):
    for item in items:
        items.remove(item)
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    mutation_findings = [f for f in findings if f["rule_name"] == "mutation_during_iteration"]
    assert len(mutation_findings) == 1
    assert "mutated" in mutation_findings[0]["message"]

def test_ast_unsafe_global_mutation_detection():
    code = """
counter = 0

def increment():
    global counter
    counter = counter + 1
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    global_findings = [f for f in findings if f["rule_name"] == "unsafe_global_mutation"]
    assert len(global_findings) == 1
    assert "counter" in global_findings[0]["message"]

def test_ast_recursion_risk_detection():
    code = """
def bad_recursion(n):
    return bad_recursion(n - 1)
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    recursion_findings = [f for f in findings if f["rule_name"] == "recursion_risk"]
    assert len(recursion_findings) == 1
    assert "lacks a structural termination condition" in recursion_findings[0]["message"]

def test_ast_async_misuse_detection():
    code = """
import time
import requests

async def get_data():
    time.sleep(1)
    requests.get("https://example.com")
"""
    parser = PythonASTParser()
    res = parser.parse(code, [])
    findings = res["ast_rules_findings"]
    
    async_findings = [f for f in findings if f["rule_name"] == "async_misuse"]
    assert len(async_findings) >= 2
    
    messages = [f["message"] for f in async_findings]
    assert any("time.sleep" in m for m in messages)
    assert any("requests.get" in m for m in messages)

def test_ast_fault_isolation():
    parser = PythonASTParser()
    
    # We pass a faulty function that raises an exception to check run_ast_rule robustness
    def faulty_rule(tree):
        raise ValueError("Simulated AST traversal failure")

    # Run inside try-except isolation wrapper
    results = parser._run_ast_rule("faulty_rule", faulty_rule, None)
    
    # Verify that the failure was isolated, returned an empty list, and didn't crash
    assert results == []
