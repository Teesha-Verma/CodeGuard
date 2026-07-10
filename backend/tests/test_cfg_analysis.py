import pytest
import ast
from app.analysis.cfg.cfg_builder import CFGBuilder

def test_cfg_sequential():
    code = """
def simple_seq():
    x = 1
    y = 2
    z = x + y
"""
    tree = ast.parse(code)
    func_node = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func_node)
    
    # 1 entry, 1 exit, 1 statement block
    assert len(cfg.nodes) == 3
    assert cfg.entry_node is not None
    assert cfg.exit_node is not None
    
    # Check paths
    path = cfg.find_path("ENTRY", "EXIT")
    assert path is not None
    assert len(path) == 3


def test_cfg_if_else():
    code = """
def check_cond(val):
    if val > 10:
        x = 1
    else:
        x = 2
    return x
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    # ENTRY -> block_1 (if condition)
    # block_1 -> block_2 (True branch) -> block_4 (join) -> block_5 (return) -> EXIT
    # block_1 -> block_3 (False branch) -> block_4 (join) -> block_5 (return) -> EXIT
    assert len(cfg.nodes) >= 6
    assert cfg.find_path("ENTRY", "EXIT") is not None
    
    # Verify True and False outgoing edges exist from the branch node
    branch_nodes = [node for node in cfg.nodes.values() if node.kind == "cfg_branch"]
    assert len(branch_nodes) == 1
    branch_node = branch_nodes[0]
    
    outgoing = cfg.get_outgoing_edges(branch_node.id)
    assert len(outgoing) == 2
    labels = {edge.label for edge in outgoing}
    assert labels == {"True", "False"}


def test_cfg_while_break_continue():
    code = """
def loop_test():
    x = 0
    while x < 10:
        x += 1
        if x == 5:
            continue
        if x == 8:
            break
    return x
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    assert cfg.find_path("ENTRY", "EXIT") is not None


def test_cfg_unreachable_code():
    code = """
def unreachable_test():
    x = 1
    return x
    y = 2  # Unreachable statement
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    unreachable = cfg.find_unreachable_code()
    assert len(unreachable) == 1
    assert any(isinstance(stmt, ast.Assign) and stmt.targets[0].id == "y" for node in unreachable for stmt in node.block.statements)


def test_cfg_dead_branches():
    code = """
def dead_branch_test():
    if False:
        x = 1
    else:
        x = 2
        
    while False:
        y = 3
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    dead_nodes = cfg.find_dead_branches()
    assert len(dead_nodes) >= 2
    
    # Verify that the body of `if False:` and body of `while False:` are caught as dead
    labels = [node.label for node in dead_nodes]
    # Check that we have statement blocks inside the dead branches
    assert len(labels) >= 2


def test_cfg_missing_return_paths():
    code = """
def missing_return(val):
    if val > 10:
        return 1
    # Fall-through path returns None implicitly
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    missing = cfg.find_missing_return_paths()
    assert len(missing) == 1


def test_cfg_complexity():
    code = """
def complex_branching(val):
    if val == 1:
        return 1
    elif val == 2:
        return 2
    elif val == 3:
        return 3
    return 4
"""
    tree = ast.parse(code)
    func = tree.body[0]
    
    builder = CFGBuilder()
    cfg = builder.build(func)
    
    complexity = cfg.get_cyclomatic_complexity()
    # 3 IF statements + 1 default -> complexity should be 4
    assert complexity == 4
    assert cfg.find_excessive_branching(threshold=2) is True
    assert cfg.find_excessive_branching(threshold=5) is False
