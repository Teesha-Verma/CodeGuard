from typing import Dict, List, Set, Optional, Generator
from app.analysis.graph.graph_node import GraphNode
from app.analysis.graph.graph_edge import GraphEdge

class Graph:
    """Base directed graph representation with traversal and query helpers."""
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        # Adjacency maps for fast lookups
        self._successors: Dict[str, List[GraphEdge]] = {}
        self._predecessors: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        if node.id not in self.nodes:
            self.nodes[node.id] = node
            self._successors[node.id] = []
            self._predecessors[node.id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        # Ensure source and target nodes exist in the graph
        if edge.source not in self.nodes:
            self.add_node(GraphNode(edge.source))
        if edge.target not in self.nodes:
            self.add_node(GraphNode(edge.target))
            
        self.edges.append(edge)
        self._successors[edge.source].append(edge)
        self._predecessors[edge.target].append(edge)

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self.nodes.get(node_id)

    def get_successors(self, node_id: str) -> List[GraphNode]:
        """Returns the list of destination nodes directly reachable from node_id."""
        if node_id not in self._successors:
            return []
        return [self.nodes[edge.target] for edge in self._successors[node_id] if edge.target in self.nodes]

    def get_predecessors(self, node_id: str) -> List[GraphNode]:
        """Returns the list of source nodes that directly link to node_id."""
        if node_id not in self._predecessors:
            return []
        return [self.nodes[edge.source] for edge in self._predecessors[node_id] if edge.source in self.nodes]

    def get_outgoing_edges(self, node_id: str) -> List[GraphEdge]:
        return self._successors.get(node_id, [])

    def get_incoming_edges(self, node_id: str) -> List[GraphEdge]:
        return self._predecessors.get(node_id, [])

    def dfs(self, start_id: str) -> Generator[GraphNode, None, None]:
        """Performs a depth-first traversal starting from start_id."""
        visited: Set[str] = set()
        stack: List[str] = [start_id]
        
        while stack:
            current_id = stack.pop()
            if current_id not in visited:
                visited.add(current_id)
                node = self.get_node(current_id)
                if node:
                    yield node
                    # Add successors in reverse order to maintain standard left-to-right processing if order is stable
                    for succ in reversed(self.get_successors(current_id)):
                        if succ.id not in visited:
                            stack.append(succ.id)

    def bfs(self, start_id: str) -> Generator[GraphNode, None, None]:
        """Performs a breadth-first traversal starting from start_id."""
        visited: Set[str] = {start_id}
        queue: List[str] = [start_id]
        
        while queue:
            current_id = queue.pop(0)
            node = self.get_node(current_id)
            if node:
                yield node
                for succ in self.get_successors(current_id):
                    if succ.id not in visited:
                        visited.add(succ.id)
                        queue.append(succ.id)

    def find_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Finds a path from start_id to end_id using BFS. Returns list of node IDs."""
        if start_id not in self.nodes or end_id not in self.nodes:
            return None
        if start_id == end_id:
            return [start_id]
            
        queue: List[List[str]] = [[start_id]]
        visited: Set[str] = {start_id}
        
        while queue:
            path = queue.pop(0)
            current_id = path[-1]
            
            for succ in self.get_successors(current_id):
                if succ.id == end_id:
                    return path + [end_id]
                if succ.id not in visited:
                    visited.add(succ.id)
                    queue.append(path + [succ.id])
        return None

    def has_cycle(self) -> bool:
        """Detects if the graph contains any cycles using DFS coloring (white/gray/black)."""
        # status: 0 = unvisited (white), 1 = visiting (gray), 2 = visited (black)
        status: Dict[str, int] = {node_id: 0 for node_id in self.nodes}
        
        def dfs_visit(node_id: str) -> bool:
            status[node_id] = 1  # visiting
            for succ in self.get_successors(node_id):
                if status[succ.id] == 1:
                    return True  # found gray node -> cycle!
                if status[succ.id] == 0:
                    if dfs_visit(succ.id):
                        return True
            status[node_id] = 2  # visited
            return False

        for node_id in self.nodes:
            if status[node_id] == 0:
                if dfs_visit(node_id):
                    return True
        return False
