import pytest
from app.analysis.graph.graph_types import NodeKind, EdgeKind
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_edge import GraphEdge
from app.analysis.graph.graph_base import Graph

def test_node_edge_creation():
    node = GraphNode(node_id="N1", kind=NodeKind.GENERIC, label="Node 1", properties={"attr": 42})
    assert node.id == "N1"
    assert node.kind == NodeKind.GENERIC
    assert node.label == "Node 1"
    assert node.properties["attr"] == 42

    edge = GraphEdge(source="N1", target="N2", kind=EdgeKind.GENERIC, label="links", properties={"weight": 1})
    assert edge.source == "N1"
    assert edge.target == "N2"
    assert edge.kind == EdgeKind.GENERIC
    assert edge.label == "links"
    assert edge.properties["weight"] == 1


def test_graph_operations():
    g = Graph()
    n1 = GraphNode("N1")
    n2 = GraphNode("N2")
    g.add_node(n1)
    g.add_node(n2)
    
    assert g.get_node("N1") == n1
    assert g.get_node("N2") == n2
    
    e1 = GraphEdge("N1", "N2")
    g.add_edge(e1)
    
    assert e1 in g.edges
    assert g.get_successors("N1") == [n2]
    assert g.get_predecessors("N2") == [n1]


def test_graph_traversal():
    # Construct a DAG:
    #     N1
    #    /  \
    #   N2  N3
    #    \  /
    #     N4
    g = Graph()
    g.add_edge(GraphEdge("N1", "N2"))
    g.add_edge(GraphEdge("N1", "N3"))
    g.add_edge(GraphEdge("N2", "N4"))
    g.add_edge(GraphEdge("N3", "N4"))
    
    bfs_nodes = [n.id for n in g.bfs("N1")]
    assert bfs_nodes[0] == "N1"
    assert set(bfs_nodes[1:3]) == {"N2", "N3"}
    assert bfs_nodes[3] == "N4"

    dfs_nodes = [n.id for n in g.dfs("N1")]
    assert dfs_nodes[0] == "N1"
    assert set(dfs_nodes) == {"N1", "N2", "N3", "N4"}


def test_find_path():
    g = Graph()
    g.add_edge(GraphEdge("A", "B"))
    g.add_edge(GraphEdge("B", "C"))
    g.add_edge(GraphEdge("C", "D"))
    
    path = g.find_path("A", "D")
    assert path == ["A", "B", "C", "D"]
    
    no_path = g.find_path("D", "A")
    assert no_path is None


def test_cycle_detection():
    # A -> B -> C -> A
    g_cycle = Graph()
    g_cycle.add_edge(GraphEdge("A", "B"))
    g_cycle.add_edge(GraphEdge("B", "C"))
    g_cycle.add_edge(GraphEdge("C", "A"))
    assert g_cycle.has_cycle() is True

    # A -> B -> C
    g_no_cycle = Graph()
    g_no_cycle.add_edge(GraphEdge("A", "B"))
    g_no_cycle.add_edge(GraphEdge("B", "C"))
    assert g_no_cycle.has_cycle() is False
