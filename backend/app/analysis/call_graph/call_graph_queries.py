from typing import List, Set, Tuple
from app.analysis.call_graph.call_graph import CallGraph

def get_callers(graph: CallGraph, function_name: str) -> List[str]:
    """Returns the names of all functions/methods that directly call the given function."""
    predecessors = graph.get_predecessors(function_name)
    return [node.id for node in predecessors]

def get_callees(graph: CallGraph, function_name: str) -> List[str]:
    """Returns the names of all functions/methods directly called by the given function."""
    successors = graph.get_successors(function_name)
    return [node.id for node in successors]

def get_reachable_functions(graph: CallGraph, function_name: str) -> Set[str]:
    """Returns the set of all function names transitively reachable from the starting function via call edges."""
    if function_name not in graph.nodes:
        return set()
    reachable = set()
    for node in graph.bfs(function_name):
        if node.id != function_name:
            reachable.add(node.id)
    return reachable

def get_degree(graph: CallGraph, function_name: str) -> Tuple[int, int]:
    """Returns a tuple of (in_degree, out_degree) for the given function name."""
    in_edges = graph.get_incoming_edges(function_name)
    out_edges = graph.get_outgoing_edges(function_name)
    return len(in_edges), len(out_edges)
