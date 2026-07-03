import pytest
from app.analysis.call_graph.call_graph_builder import CallGraphBuilder
from app.analysis.call_graph.call_graph_queries import (
    get_callers,
    get_callees,
    get_reachable_functions,
    get_degree,
)

def test_call_graph_direct_calls():
    sources = {
        "main": """
def step_a():
    pass

def step_b():
    step_a()

def run():
    step_b()
"""
    }
    
    builder = CallGraphBuilder()
    cg = builder.build(sources)
    
    # Check nodes
    assert "main.step_a" in cg.nodes
    assert "main.step_b" in cg.nodes
    assert "main.run" in cg.nodes
    
    # Check direct callees
    assert get_callees(cg, "main.run") == ["main.step_b"]
    assert get_callees(cg, "main.step_b") == ["main.step_a"]
    assert get_callees(cg, "main.step_a") == []

    # Check callers
    assert get_callers(cg, "main.step_a") == ["main.step_b"]
    assert get_callers(cg, "main.step_b") == ["main.run"]
    
    # Reachability
    assert get_reachable_functions(cg, "main.run") == {"main.step_b", "main.step_a"}
    
    # Degree
    in_deg, out_deg = get_degree(cg, "main.step_b")
    assert in_deg == 1
    assert out_deg == 1


def test_call_graph_imports_and_classes():
    sources = {
        "utils": """
def helper():
    return 42
""",
        "models": """
from utils import helper

class DB:
    def save(self):
        helper()
""",
        "app": """
from models import DB
import utils

def main():
    db = DB()
    db.save()
    utils.helper()
"""
    }
    
    builder = CallGraphBuilder()
    cg = builder.build(sources)
    
    # Check function/method nodes
    assert "utils.helper" in cg.nodes
    assert "models.DB.save" in cg.nodes
    assert "app.main" in cg.nodes
    
    # Verify app.main calls models.DB.save (resolved via local variable type DB)
    assert "models.DB.save" in get_callees(cg, "app.main")
    
    # Verify app.main calls utils.helper (resolved via imported module attribute)
    assert "utils.helper" in get_callees(cg, "app.main")
    
    # Verify models.DB.save calls utils.helper (resolved via from import)
    assert "utils.helper" in get_callees(cg, "models.DB.save")
    
    # Verify transitive reachability from app.main
    reachable = get_reachable_functions(cg, "app.main")
    assert "models.DB.save" in reachable
    assert "utils.helper" in reachable
