from typing import Dict, Any, List
from app.api.schemas import ReviewIssue, FileReport
from app.reasoning.root_cause_engine import RootCauseEngine
from app.reasoning.confidence_engine import ConfidenceEngine
from app.static_analysis.context_resolver import ContextResolver
from app.static_analysis.prioritization import PrioritizationEngine
from app.core.config import get_settings

class ReviewGenerator:
    """Assembles localized static analysis findings, coordinates AI grounding, and builds structured ReviewIssues."""
    
    def __init__(self, review_id: str):
        self.review_id = review_id
        self.root_cause_engine = RootCauseEngine(review_id)
        self.traces = []

    def generate(self, aggregated: Dict[str, Any]) -> List[ReviewIssue]:
        """
        Groups all deterministic findings by line, merges AST + linter evidence,
        and generates grounded AI analysis for each.
        """
        findings_by_line = {}
        changed_lines_set = set(aggregated.get("changed_lines", []))
        
        # 1. Gather AST Mutation Detections (from old MutationDetector)
        mutation_analysis = aggregated.get("mutation_analysis", [])
        for item in mutation_analysis:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
                
            pattern = item.get("pattern", "list mutation during iteration")
            msg = item.get("message", "List mutation during iteration")
            
            findings_by_line[line] = {
                "line": line,
                "issue": msg,
                "severity": "high" if "shared" in pattern else "critical",
                "issue_type": "runtime_logic_error",
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "Loop" if "list" in pattern else "Class",
                        "line": line,
                        "pattern": pattern,
                        "message": msg,
                        "evidence_strength": 1.0
                    }],
                    "linter_rules": [],
                    "trigger_lines": [line]
                }
            }

        # 2. Gather AST Scope Tracker findings
        scope_analysis = aggregated.get("scope_analysis", [])
        for item in scope_analysis:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
                
            pattern = item.get("pattern", "variable_shadowing")
            msg = item.get("message", "Shadowing variable")
            strength = 0.3 if "shadow" in pattern else 0.7
            
            node_obj = {
                "node_type": "Assign",
                "line": line,
                "pattern": pattern,
                "message": msg,
                "evidence_strength": strength
            }
            
            if line in findings_by_line:
                if "ast" not in findings_by_line[line]["sources"]:
                    findings_by_line[line]["sources"].append("ast")
                findings_by_line[line]["evidence"]["ast_nodes"].append(node_obj)
            else:
                findings_by_line[line] = {
                    "line": line,
                    "issue": msg,
                    "severity": "medium",
                    "issue_type": "code_smell",
                    "sources": ["ast"],
                    "evidence": {
                        "ast_nodes": [node_obj],
                        "linter_rules": [],
                        "trigger_lines": [line]
                    }
                }

        # 3. Gather AST Async warnings
        ast_struct = aggregated.get("ast_structural_metadata", {})
        async_issues = ast_struct.get("async_issues", []) if isinstance(ast_struct, dict) else []
        for item in async_issues:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
                
            pattern = item.get("type", "async_missing_await")
            msg = item.get("message", "Async issue")
            
            node_obj = {
                "node_type": "AsyncDef/Call",
                "line": line,
                "pattern": pattern,
                "message": msg,
                "evidence_strength": 0.8
            }
            
            if line in findings_by_line:
                if "ast" not in findings_by_line[line]["sources"]:
                    findings_by_line[line]["sources"].append("ast")
                findings_by_line[line]["evidence"]["ast_nodes"].append(node_obj)
            else:
                findings_by_line[line] = {
                    "line": line,
                    "issue": msg,
                    "severity": "high",
                    "issue_type": "concurrency",
                    "sources": ["ast"],
                    "evidence": {
                        "ast_nodes": [node_obj],
                        "linter_rules": [],
                        "trigger_lines": [line]
                    }
                }

        # 4. Gather Linter Findings
        linter_findings = aggregated.get("linter_findings", [])
        for f in linter_findings:
            line = f.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
                
            tool = f.get("tool", "linter")
            rule = f.get("rule", "")
            msg = f.get("message", "")
            sev = f.get("severity", "medium").lower()
            
            rule_obj = {
                "tool": tool,
                "rule_id": rule,
                "line": line,
                "message": msg
            }
            
            if line in findings_by_line:
                if tool not in findings_by_line[line]["sources"]:
                    findings_by_line[line]["sources"].append(tool)
                findings_by_line[line]["evidence"]["linter_rules"].append(rule_obj)
            else:
                findings_by_line[line] = {
                    "line": line,
                    "issue": msg,
                    "severity": sev,
                    "issue_type": "security" if tool == "bandit" else "code_smell",
                    "sources": [tool],
                    "evidence": {
                        "ast_nodes": [],
                        "linter_rules": [rule_obj],
                        "trigger_lines": [line]
                    }
                }

        # 5. Gather AST Heuristic Findings (from HeuristicEngine)
        heuristic_findings = aggregated.get("heuristic_findings", [])
        for item in heuristic_findings:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
                
            rule_name = item.get("rule_name", "")
            msg = item.get("message", "")
            sev = item.get("severity", "medium")
            issue_type = item.get("issue_type", "runtime_logic_error")
            strength = item.get("evidence_strength", 0.8)
            
            node_obj = {
                "node_type": "HeuristicNode",
                "line": line,
                "pattern": rule_name,
                "message": msg,
                "evidence_strength": strength
            }
            
            if line in findings_by_line:
                if "ast" not in findings_by_line[line]["sources"]:
                    findings_by_line[line]["sources"].append("ast")
                findings_by_line[line]["evidence"]["ast_nodes"].append(node_obj)
                
                # Upgrade severity and description if heuristic is higher severity
                current_sev = findings_by_line[line]["severity"].lower()
                new_sev = sev.lower()
                sev_order = {"low": 1, "medium": 2, "high": 3, "critical": 4}
                if sev_order.get(new_sev, 0) > sev_order.get(current_sev, 0):
                    findings_by_line[line]["severity"] = sev
                    findings_by_line[line]["issue_type"] = issue_type
                    findings_by_line[line]["issue"] = msg
            else:
                findings_by_line[line] = {
                    "line": line,
                    "issue": msg,
                    "severity": sev,
                    "issue_type": issue_type,
                    "sources": ["ast"],
                    "evidence": {
                        "ast_nodes": [node_obj],
                        "linter_rules": [],
                        "trigger_lines": [line]
                    }
                }

        # Resolve file-level context
        file_path = aggregated.get("file_path", "")
        context_meta = ContextResolver.resolve(file_path)
        settings = get_settings()
        threshold = settings.REASONING_ACTIVATION_THRESHOLD

        # 6. Coordinate AI Grounding and Confidence calculations
        final_issues = []
        for line, finding in sorted(findings_by_line.items()):
            # A: Calculate evidence strength for the line
            evidence_strength = 0.5  # default
            
            # Check AST nodes
            ast_nodes = finding["evidence"].get("ast_nodes", [])
            ast_strengths = []
            for node in ast_nodes:
                if "evidence_strength" in node:
                    ast_strengths.append(node["evidence_strength"])
                else:
                    pattern = node.get("pattern", "").lower()
                    rule = node.get("rule_name", "").lower()
                    if "mutation" in pattern or "mutation" in rule:
                        ast_strengths.append(1.0)
                    elif "eval" in pattern or "exec" in pattern or "dangerous" in pattern or "dangerous" in rule:
                        ast_strengths.append(1.0)
                    elif "mutable_default" in pattern or "mutable_default" in rule:
                        ast_strengths.append(1.0)
                    elif "broad_except" in pattern or "broad_except" in rule:
                        ast_strengths.append(0.9)
                    elif "async" in pattern or "async" in rule:
                        ast_strengths.append(0.8)
                    elif "recursion" in pattern or "recursion" in rule:
                        ast_strengths.append(0.8)
                    elif "global" in pattern or "global" in rule:
                        ast_strengths.append(0.8)
                    elif "shadow" in pattern or "shadow" in rule:
                        ast_strengths.append(0.3)
                    elif "nesting" in pattern or "nesting" in rule:
                        ast_strengths.append(0.7)
                    else:
                        ast_strengths.append(0.6)
            if ast_strengths:
                evidence_strength = max(ast_strengths)
                
            # Check linter rules
            linter_rules = finding["evidence"].get("linter_rules", [])
            linter_strengths = []
            for r in linter_rules:
                tool = r.get("tool", "").lower()
                rule_id = r.get("rule_id", "").upper()
                msg = r.get("message", "").lower()
                if (
                    rule_id in PrioritizationEngine.STYLE_CODES
                    or "line too long" in msg
                    or "whitespace" in msg
                    or "missing docstring" in msg
                    or "indentation" in msg
                    or "formatting" in msg
                ):
                    linter_strengths.append(0.2)
                elif tool == "bandit" or "security" in msg or "vulnerability" in msg:
                    linter_strengths.append(0.9)
                else:
                    linter_strengths.append(0.6)
            if linter_strengths:
                if ast_strengths:
                    evidence_strength = max(evidence_strength, max(linter_strengths))
                    # Overlap boost
                    evidence_strength = min(1.0, evidence_strength + 0.1)
                else:
                    evidence_strength = max(linter_strengths)

            # Resolve primary source and rule for prioritization and static explanations
            primary_source = "ast"
            primary_rule = ""
            primary_msg = finding["issue"]
            
            if finding["evidence"]["linter_rules"]:
                rule_obj = finding["evidence"]["linter_rules"][0]
                primary_source = rule_obj.get("tool", "linter")
                primary_rule = rule_obj.get("rule_id", "")
                primary_msg = rule_obj.get("message", finding["issue"])
            elif finding["evidence"]["ast_nodes"]:
                node_obj = finding["evidence"]["ast_nodes"][0]
                primary_source = "ast"
                primary_rule = node_obj.get("pattern", node_obj.get("rule_name", ""))
                primary_msg = node_obj.get("message", finding["issue"])

            # B: Conditionally activate AI reasoning
            reasoning_activated = evidence_strength >= threshold
            if reasoning_activated:
                ai_details = self.root_cause_engine.analyze_finding(finding, aggregated)
                reasoning_source = "llm"
            else:
                ai_details = self._generate_static_explanation(finding, primary_rule, primary_msg)
                reasoning_source = "static_analysis"

            priority_info = PrioritizationEngine.analyze(
                source=primary_source,
                rule_id=primary_rule,
                message=primary_msg,
                context_meta=context_meta
            )
            
            # C: Confidence calculation with is_changed tracking
            is_changed = line in changed_lines_set if changed_lines_set else True
            conf_details = ConfidenceEngine.calculate(
                finding, 
                finding["sources"], 
                finding["evidence"],
                context_meta=context_meta,
                signal_meta=priority_info,
                is_changed=is_changed
            )
            
            # D: Calculate unified priority_score
            sev = priority_info.get("signal_priority", finding["severity"]).lower()
            sev_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2}
            severity_weight = sev_weights.get(sev, 0.5)
            
            changed_code_boost_val = 1.0 if is_changed else 0.0
            
            issue_cat = priority_info.get("issue_category", "runtime logic risks").lower()
            if issue_cat == "security" or sev == "critical":
                execution_risk = 1.0
            elif issue_cat == "mutation risks" or issue_cat == "async misuse" or issue_cat == "runtime logic risks":
                execution_risk = 0.8
            elif issue_cat == "style-only violations" or priority_info.get("is_low_signal"):
                execution_risk = 0.1
            else:
                execution_risk = 0.3
                
            priority_score = (
                severity_weight * 0.3 + 
                conf_details["confidence"] * 0.25 + 
                evidence_strength * 0.25 + 
                changed_code_boost_val * 0.15 + 
                execution_risk * 0.05
            )
            priority_score = round(max(0.10, min(1.0, priority_score)), 2)

            # E: Separate source attribution fields
            detection_sources = list(set(finding["sources"]))
            sources_compat = detection_sources + [reasoning_source]
            
            # F: Trace expansion
            trace_chain = conf_details["reasons"].copy()
            trace_chain.append(f"Evidence strength calculated: {evidence_strength:.2f}")
            trace_chain.append(f"Reasoning activation threshold: {threshold:.2f}")
            trace_chain.append(f"Reasoning engine activated: {reasoning_activated}")
            if reasoning_activated:
                trace_chain.append(f"LLM generated explanations grounded on {', '.join(detection_sources)}")
            else:
                trace_chain.append("Bypassed LLM reasoning. Static analysis explanation generated.")
            
            issue = ReviewIssue(
                line=line,
                severity=priority_info.get("signal_priority", finding["severity"]),
                confidence=conf_details["confidence"],
                issue=finding["issue"],
                root_cause=ai_details.get("root_cause", ""),
                trigger_condition=ai_details.get("trigger_condition", ""),
                fix=ai_details.get("fix", ""),
                patch=ai_details.get("patch") or None,
                issue_type=ai_details.get("issue_type", finding["issue_type"]),
                sources=sources_compat,
                reasoning_trace=trace_chain,
                evidence=finding["evidence"],
                signal_priority=priority_info.get("signal_priority", "medium"),
                issue_category=priority_info.get("issue_category", "runtime logic risks"),
                is_low_signal=priority_info.get("is_low_signal", False),
                detection_source=primary_source,
                reasoning_source=reasoning_source,
                priority_score=priority_score,
                detection_sources=detection_sources
            )
            final_issues.append(issue)

            # Record Trace
            self.traces.append({
                "stage": "confidence_and_grounding",
                "duration_ms": 0.0,
                "input_data": {
                    "line": line,
                    "sources": detection_sources,
                    "evidence": finding["evidence"]
                },
                "output_data": {
                    "arithmetic_steps": trace_chain,
                    "confidence_score": conf_details["confidence"],
                    "evidence_strength": evidence_strength,
                    "reasoning_activated": reasoning_activated,
                    "priority_score": priority_score,
                    "source_attributions": {
                        "linters": [r.get("tool") for r in finding["evidence"]["linter_rules"]],
                        "ast_patterns": [n.get("pattern", n.get("rule_name", "")) for n in finding["evidence"]["ast_nodes"]]
                    }
                }
            })
            
        # Sort issues descending by priority score
        final_issues.sort(key=lambda x: x.priority_score, reverse=True)
        return final_issues

    def _generate_static_explanation(self, finding: Dict[str, Any], primary_rule: str, primary_msg: str) -> Dict[str, Any]:
        rule = str(primary_rule).upper()
        msg = str(primary_msg)
        line = finding.get("line", 1)
        
        # Defaults
        root_cause = f"A minor style warning was flagged on line {line}: {msg}."
        trigger_condition = "This is triggered to capture style-only issues that do not affect runtime execution."
        fix = f"Refactor the code on line {line} to satisfy general static analysis rules."
        
        # 1. Line too long (E501 / C0301)
        if "E501" in rule or "C0301" in rule or "line too long" in msg.lower():
            limit_info = ""
            if ">" in msg:
                import re
                after_gt = msg.split('>')[-1].strip()
                match = re.search(r'\d+', after_gt)
                if match:
                    limit_info = f" (limit: {match.group(0)} characters)"
            root_cause = f"This line on line {line} exceeds the configured limit{limit_info}, which can reduce code readability and make side-by-side diff reviews harder."
            trigger_condition = "Occurs when a line exceeds the maximum recommended character limit."
            fix = "Consider splitting this line into logical segments, extracting complex expressions into helper variables, or wrapping long method parameters."
            
        # 2. Whitespace / Indentation / Empty lines
        elif any(x in rule for x in ("E301", "E302", "E303", "E305", "E2", "W291", "W292", "W293", "W391", "C0303", "C0325", "C0326", "C0304", "C0305")):
            root_cause = f"Operator padding or trailing whitespace on line {line} deviates from clean coding conventions."
            trigger_condition = "Flags trailing whitespace or inconsistent line spacing that violates formatting standards."
            fix = "Trim the trailing whitespace or adjust spacing around operators to maintain standard codebase formatting."
            
        # 3. Missing docstrings
        elif any(x in rule for x in ("C0114", "C0115", "C0116")):
            root_cause = f"The public component on line {line} lacks inline documentation. Clear docstrings make public APIs significantly easier to maintain."
            trigger_condition = "Flags public modules, classes, or functions that do not declare a descriptive docstring."
            fix = "Add a concise docstring summarizing the component's purpose, arguments, and return types."
 
        # 4. Radon Nesting / Heuristics
        elif "NESTING" in rule or "nesting" in msg.lower():
            root_cause = f"The logic on line {line} has deep structural nesting, which increases cognitive load and hampers readability."
            trigger_condition = "Triggered when nested block structures exceed standard nesting limits."
            fix = "Refactor deep nesting by returning early with guard clauses or extracting inner logic blocks into separate helper methods."
            
        # 5. Shadowing (when suppressed / low confidence)
        elif "SHADOWING" in rule or "shadow" in msg.lower():
            root_cause = f"A variable definition on line {line} shadows a built-in function or an identifier in an outer scope."
            trigger_condition = "Occurs when a local scope declaration overrides a symbol in a parent namespace."
            fix = "Rename this identifier to avoid name collisions and protect against subtle runtime scoping issues."
            
        # 6. Global modification
        elif "GLOBAL" in rule or "global" in msg.lower():
            root_cause = f"Directly mutating a global variable on line {line} creates hidden side-effects and reduces modular testability."
            trigger_condition = "Flags usage of the 'global' declaration inside functions to mutate external state."
            fix = "Re-architect the function to accept the global variable as an input parameter and return the updated value."
            
        return {
            "root_cause": root_cause,
            "trigger_condition": trigger_condition,
            "fix": fix,
            "patch": None,
            "issue_type": finding.get("issue_type", "style")
        }
