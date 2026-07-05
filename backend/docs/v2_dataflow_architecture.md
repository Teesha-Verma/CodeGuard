# CodeGuard V2 — Data Flow Analysis Architecture

## Overview

The Data Flow Analysis Layer is a **deterministic** security analysis infrastructure that tracks how data moves through Python codebases. It performs taint analysis to detect vulnerabilities such as SQL injection, command injection, unsafe deserialization, and more — all without AI/LLM involvement.

## Design Principles

1. **Deterministic** — Every detection is based on concrete AST patterns and graph traversals. No AI/ML in the detection pipeline.
2. **Reuse-First** — Built on top of the shared Graph Foundation (`app/analysis/graph/`). `DataFlowGraph` subclasses `Graph`; `DataFlowNode` subclasses `GraphNode`; `DataFlowEdge` subclasses `GraphEdge`.
3. **Modular** — Separated into independent subsystems (graph construction, propagation, taint detection, vulnerability rules).
4. **Cross-Boundary** — Supports intra-function, inter-function, and cross-file taint tracking via graph merging.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   DataFlow Package                          │
│  app/analysis/dataflow/                                     │
│                                                             │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────────┐ │
│  │  constants.py │  │   models.py    │  │                 │ │
│  │  - NodeKinds  │  │  - TaintLabel  │  │                 │ │
│  │  - EdgeKinds  │  │  - FlowPath    │  │                 │ │
│  │  - TaintKind  │  │  - VulnFinding │  │                 │ │
│  │  - Severity   │  │                │  │                 │ │
│  └──────────────┘  └────────────────┘  │                 │ │
│                                         │                 │ │
│  ┌─────────────────────────────────────┐│  ┌───────────┐ │ │
│  │  graph/                             ││  │  taint/   │ │ │
│  │  ┌──────────────────┐               ││  │           │ │ │
│  │  │ DataFlowNode     │←─ GraphNode   ││  │ Source    │ │ │
│  │  │ DataFlowEdge     │←─ GraphEdge   ││  │ Detector  │ │ │
│  │  │ DataFlowGraph    │←─ Graph       ││  │           │ │ │
│  │  │ DataFlowBuilder  │  (AST Walker) ││  │ Sink      │ │ │
│  │  └──────────────────┘               ││  │ Detector  │ │ │
│  └─────────────────────────────────────┘│  │           │ │ │
│                                         │  │ Taint     │ │ │
│  ┌─────────────────────────────────────┐│  │ Engine    │ │ │
│  │  propagation/                       ││  │           │ │ │
│  │  ┌──────────────────┐               ││  │ Vuln      │ │ │
│  │  │ AliasTracker     │               ││  │ Rules     │ │ │
│  │  │ PropagationEngine│               ││  └───────────┘ │ │
│  │  │ FlowQueries      │               ││                 │ │
│  │  └──────────────────┘               ││                 │ │
│  └─────────────────────────────────────┘│                 │ │
│                                         └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│            Shared Graph Foundation (V2)                      │
│  app/analysis/graph/                                         │
│  - GraphNode, GraphEdge, Graph                               │
│  - BFS, DFS, find_path, has_cycle                            │
└─────────────────────────────────────────────────────────────┘
```

## Package Structure

```
app/analysis/dataflow/
├── __init__.py              # Top-level exports
├── constants.py             # Enums: node/edge kinds, taint kinds, severity
├── models.py                # Dataclasses: TaintLabel, FlowPath, VulnerabilityFinding
│
├── graph/
│   ├── __init__.py
│   ├── dataflow_node.py     # DataFlowNode (extends GraphNode)
│   ├── dataflow_edge.py     # DataFlowEdge (extends GraphEdge)
│   ├── dataflow_graph.py    # DataFlowGraph (extends Graph)
│   └── dataflow_builder.py  # AST → DataFlowGraph builder
│
├── propagation/
│   ├── __init__.py
│   ├── propagation_models.py  # PropagationChain, PropagationStep
│   ├── alias_tracker.py       # Variable aliasing tracker
│   ├── propagation_engine.py  # Forward taint propagation
│   └── flow_queries.py        # High-level query API
│
└── taint/
    ├── __init__.py
    ├── source_detector.py     # Pattern-based source detection
    ├── sink_detector.py       # Pattern-based sink detection
    ├── taint_engine.py        # End-to-end taint orchestrator
    └── vulnerability_rules.py # Vulnerability rule definitions
```

## Component Details

### 1. Graph Infrastructure (`graph/`)

#### DataFlowNode
Extends `GraphNode` with:
- `df_kind` — distinguishes variables, parameters, literals, return values, attributes, collection elements, call results, imports
- `taint_labels` — set of `TaintLabel` objects
- `is_source` / `is_sink` — boolean markers
- Serialization via `to_dict()`

#### DataFlowEdge
Extends `GraphEdge` with:
- `df_kind` — assignment, parameter pass, return propagation, alias, attribute write, collection write, function call, augmented assign, tuple unpack

#### DataFlowGraph
Extends `Graph` (inherits BFS, DFS, `find_path`, `has_cycle`). Adds:
- `trace_flow()` — all reachable nodes from a starting point
- `find_flow_between()` — find path between two nodes
- `get_sources()` / `get_sinks()` / `get_tainted_nodes()`
- `get_nodes_by_kind()` / `get_nodes_by_name()`
- `to_dict()` serialization

#### DataFlowBuilder
AST walker that constructs the graph. Handles:
- Simple assignments (`x = y`)
- Augmented assignments (`x += 1`)
- Tuple unpacking (`a, b = 1, 2`)
- Function parameters and return values
- Function calls with argument tracking
- Attribute writes (`self.x = val`)
- Subscript writes (`data[key] = val`)
- Classes and scoped methods
- Imports
- Control flow bodies (if/for/while/with/try)

### 2. Propagation Engine (`propagation/`)

#### AliasTracker
Records variable aliasing: when `x = y` occurs, x aliases y. Supports transitive aliasing (if y aliases z, then x also aliases z).

#### PropagationEngine
Forward propagation of taint labels through the DataFlowGraph. Algorithm:
1. Initialize worklist with all tainted nodes
2. For each tainted node, propagate labels to all successors via data-flow edges
3. Also propagate via alias relationships
4. Continue until fixpoint (no new taint)

Also provides `find_tainted_sinks()` for source→sink flow detection and `trace_chain()` for building propagation chain evidence.

#### Flow Queries
High-level API functions:
- `get_sources(graph)` / `get_sinks(graph)`
- `trace_variable(graph, name)` — all nodes reachable from a named variable
- `trace_function(graph, name)` — all nodes reachable from a function call
- `trace_to_sink(graph, source_id)` — all flow paths from source to any sink
- `trace_from_source(graph, sink_id)` — all flow paths from any source to sink
- `reachable_sinks(graph, source_id)` / `reachable_sources(graph, sink_id)`
- `has_taint_flow(graph, source_id, sink_id)` — boolean reachability check
- `get_data_dependencies(graph, node_id)` / `get_reverse_dependencies(graph, node_id)`
- `get_flow_summary(graph)` — metric counts

### 3. Taint Detection (`taint/`)

#### SourceDetector
Pattern-based detection of taint sources:
- **User Input**: `input()`, `raw_input()`, `sys.stdin.read()`
- **HTTP Parameters**: `request.args`, `request.form`, `request.json`, `request.GET`, `request.POST`
- **Environment**: `os.environ`, `os.getenv()`
- **CLI Arguments**: `sys.argv`
- **Network Input**: `socket.recv()`

#### SinkDetector
Pattern-based detection of security sinks:
- **Code Injection**: `eval()`, `exec()`, `compile()`
- **Command Injection**: `os.system()`, `subprocess.run()`, `subprocess.Popen()`
- **SQL Injection**: `cursor.execute()`, `db.execute()`
- **Unsafe Deserialization**: `pickle.loads()`, `marshal.loads()`
- **Unsafe YAML**: `yaml.load()`, `yaml.unsafe_load()`
- **SSRF**: `requests.get()`, `urllib.request.urlopen()`
- **File Access**: `open()`, `io.open()`

Supports custom sink registry via `extra_sinks` parameter.

#### TaintEngine
End-to-end orchestrator:
1. `add_module(name, source_code)` — parse modules
2. `run()` → returns `List[FlowPath]`
3. Internally: merge graphs → detect sources → detect sinks → propagate → find flows
4. Cross-module graph merging with namespace-prefixed node IDs

#### VulnerabilityRules
Maps FlowPaths to named vulnerability findings:
- `SQL_INJECTION` (Critical)
- `COMMAND_INJECTION` (Critical)
- `CODE_INJECTION` (Critical)
- `UNSAFE_DESERIALIZATION` (High)
- `PATH_TRAVERSAL` (High)
- `UNSAFE_YAML` (High)
- `SSRF` (High)
- `HARDCODED_SECRET` (Medium) — standalone node-level check

## Inheritance Chain

```
GraphNode → DataFlowNode
GraphEdge → DataFlowEdge
Graph     → DataFlowGraph
```

No graph traversal logic is duplicated — `DataFlowGraph` inherits `bfs()`, `dfs()`, `find_path()`, `has_cycle()`, `get_successors()`, `get_predecessors()`, etc. from the shared `Graph` class.

## Test Coverage

| File | Tests |
|------|-------|
| `tests/test_dataflow_graph.py` | Node, Edge, Graph, Builder, Models |
| `tests/test_dataflow_propagation.py` | AliasTracker, PropagationEngine, FlowQueries |
| `tests/test_dataflow_taint.py` | SourceDetector, SinkDetector, TaintEngine, VulnerabilityRules |
