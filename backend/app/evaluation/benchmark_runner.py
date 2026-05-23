import time
from typing import List, Dict, Any
from app.static_analysis.ast_parser import PythonASTParser
from app.static_analysis.mutation_detector import MutationDetector
from app.static_analysis.scope_tracker import ScopeTracker
from app.static_analysis.heuristic_engine import HeuristicEngine
from app.pipeline.orchestrator import PipelineOrchestrator
from app.diff.diff_parser import DiffFile

# Test repository of known buggy and safe python snippets
TEST_SUITE = [
    {
        "name": "safe_loop_and_pure_function",
        "code": """def process_items(items):
    # Safe loop: iterates over a copy using slice
    for item in items[:]:
        if item < 0:
            items.remove(item)
    return items
""",
        "is_buggy": False,
        "expected_issues": []
    },
    {
        "name": "unsafe_loop_mutation",
        "code": """def process_items(items):
    # Unsafe loop: mutates items directly during active traversal
    for item in items:
        if item < 0:
            items.remove(item)
    return items
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 5, "pattern": "list mutation during iteration"}
        ]
    },
    {
        "name": "unsafe_global_scope_modification",
        "code": """cache_hits = 0
 
def log_cache_hit():
    global cache_hits
    cache_hits += 1
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 4, "pattern": "global_modification"}
        ]
    },
    {
        "name": "safe_global_read_only",
        "code": """CONFIG_MAX = 100
 
def get_limit(factor):
    # Safe read of global variable without global keyword or write
    return CONFIG_MAX * factor
""",
        "is_buggy": False,
        "expected_issues": []
    },
    {
        "name": "variable_shadowing_warning",
        "code": """def process_data(value):
    # shadowing builtins or global variable 'value'
    value = value + 1
    return value
""",
        "is_buggy": False, # Shadows is a code smell, not a fatal bug
        "expected_issues": []
    },
    {
        "name": "safe_list_comprehension_filter",
        "code": """def filter_negatives(items):
    # Tricky but safe: list comprehension creates a new list
    positive_items = [x for x in items if x >= 0]
    return positive_items
""",
        "is_buggy": False,
        "expected_issues": []
    },
    {
        "name": "safe_recursion_with_base_case",
        "code": """def factorial(n):
    # Safe recursion: has a clear base case terminating path
    if n <= 1:
        return 1
    return n * factorial(n - 1)
""",
        "is_buggy": False,
        "expected_issues": []
    },
    {
        "name": "unsafe_mutable_default",
        "code": """def append_to(element, target=[]):
    target.append(element)
    return target
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 1, "pattern": "mutable_default"}
        ]
    },
    {
        "name": "unsafe_broad_except",
        "code": """try:
    val = int("invalid")
except Exception:
    pass
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 3, "pattern": "broad_except"}
        ]
    },
    {
        "name": "unsafe_eval",
        "code": """def execute_user_code(user_code):
    return eval(user_code)
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 2, "pattern": "dangerous_builtin"}
        ]
    },
    {
        "name": "unsafe_recursion",
        "code": """def infinite_recursion(n):
    return infinite_recursion(n)
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 1, "pattern": "recursion_risk"}
        ]
    },
    {
        "name": "unsafe_nesting",
        "code": """def deeply_nested_func(a, b, c, d):
    if a:
        if b:
            for i in range(10):
                if c:
                    print(d)
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 5, "pattern": "excessive_nesting"}
        ]
    },
    {
        "name": "unsafe_async_misuse",
        "code": """import time
async def async_worker():
    time.sleep(2)
""",
        "is_buggy": True,
        "expected_issues": [
            {"line": 2, "pattern": "async_misuse"},
            {"line": 3, "pattern": "async_misuse"}
        ]
    }
]

class BenchmarkRunner:
    """Automated evaluation harness calculating CodeGuard's precision, recall, and false positive metrics."""
    
    def __init__(self):
        self.ast_parser = PythonASTParser()
        self.mutation_detector = MutationDetector()
        self.scope_tracker = ScopeTracker()
        self.heuristic_engine = HeuristicEngine()

    def run_evaluations(self) -> Dict[str, Any]:
        """
        Runs the evaluation suite and compiles a performance metrics matrix.
        """
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        start_time = time.time()
        
        results = []
        
        for case in TEST_SUITE:
            name = case["name"]
            code = case["code"]
            is_buggy = case["is_buggy"]
            expected = case["expected_issues"]
            
            # Run deterministic analyzers
            mutations = self.mutation_detector.analyze(code)
            scope = self.scope_tracker.analyze(code)
            heuristics = self.heuristic_engine.analyze(code)
            
            # Combine findings
            detected = []
            for m in mutations:
                detected.append({"line": m["line"], "pattern": m["pattern"]})
            for s in scope:
                detected.append({"line": s["line"], "pattern": s["pattern"]})
            for h in heuristics:
                pattern_map = {
                    "mutation_during_iteration": "list mutation during iteration",
                    "mutable_default": "mutable_default",
                    "broad_except": "broad_except",
                    "dangerous_builtin": "dangerous_builtin",
                    "recursion_risk": "recursion_risk",
                    "excessive_nesting": "excessive_nesting",
                    "async_misuse": "async_misuse",
                    "global_modification": "global_modification"
                }
                pattern = pattern_map.get(h["rule_name"], h["rule_name"])
                # Avoid duplicate patterns on the same line
                if not any(d["line"] == h["line"] and d["pattern"] == pattern for d in detected):
                    detected.append({"line": h["line"], "pattern": pattern})
                
            # Compare against expected
            case_tp = 0
            case_fp = 0
            case_fn = 0
            
            expected_matched = set()
            for det in detected:
                matched = False
                for idx, exp in enumerate(expected):
                    if det["line"] == exp["line"] and det["pattern"] == exp["pattern"]:
                        matched = True
                        expected_matched.add(idx)
                        break
                if matched:
                    case_tp += 1
                else:
                    case_fp += 1
                    
            case_fn = len(expected) - len(expected_matched)
            
            if not is_buggy and len(detected) == 0:
                true_negatives += 1
            else:
                true_positives += case_tp
                false_positives += case_fp
                false_negatives += case_fn
                
            results.append({
                "case_name": name,
                "detected": detected,
                "expected": expected,
                "metrics": {
                    "true_positives": case_tp,
                    "false_positives": case_fp,
                    "false_negatives": case_fn
                }
            })
            
        duration = round(time.time() - start_time, 4)
        
        # Calculate Precision, Recall, and False Positive Rate
        precision = 1.0
        if (true_positives + false_positives) > 0:
            precision = round(true_positives / (true_positives + false_positives), 2)
            
        recall = 1.0
        if (true_positives + false_negatives) > 0:
            recall = round(true_positives / (true_positives + false_negatives), 2)
            
        false_positive_rate = 0.0
        if (false_positives + true_negatives) > 0:
            false_positive_rate = round(false_positives / (false_positives + true_negatives), 2)
            
        accuracy = round((true_positives + true_negatives) / len(TEST_SUITE), 2)
        
        metrics_summary = {
            "total_cases_evaluated": len(TEST_SUITE),
            "duration_seconds": duration,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives,
            "precision": precision,
            "recall": recall,
            "false_positive_rate": false_positive_rate,
            "accuracy": accuracy,
            "cases": results
        }
        
        return metrics_summary
 
if __name__ == "__main__":
    runner = BenchmarkRunner()
    summary = runner.run_evaluations()
    print("=== CODEGUARD V1 BENCHMARK REPORT ===")
    print(f"Total Cases Checked  : {summary['total_cases_evaluated']}")
    print(f"Precision Trend      : {summary['precision']} (track precision trends)")
    print(f"Recall Target        : {summary['recall']} (continuously improve recall)")
    print(f"False Positive Rate  : {summary['false_positive_rate']} (monitor false-positive rates)")
    print(f"Accuracy Metric      : {summary['accuracy']}")
    print(f"TP: {summary['true_positives']} | FP: {summary['false_positives']} | TN: {summary['true_negatives']} | FN: {summary['false_negatives']}")
    print("=====================================")
