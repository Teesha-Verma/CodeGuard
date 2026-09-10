import hashlib
import re
from typing import Dict, Any, List, Tuple, Optional
from app.api.schemas import ReviewIssue, FileReport
from app.reasoning.root_cause_engine import RootCauseEngine
from app.reasoning.confidence_engine import ConfidenceEngine
from app.static_analysis.context_resolver import ContextResolver
from app.static_analysis.prioritization import PrioritizationEngine
from app.analysis.RAG.knowledge_retrieval_service import KnowledgeRetrievalService
from app.core.config import get_settings
from app.llm.llm_budget import get_review_tracker
from app.diff.diff_parser import DiffParser


class ReviewGenerator:
    """Assembles localized static analysis findings, coordinates AI grounding, and builds structured ReviewIssues.

    Uses a deterministic two-phase architecture:
      Phase A (Collection): Collect ALL deterministic findings from every static analyzer into a flat list.
      Phase B (Deduplication & Ranking): Normalize, deduplicate overlapping findings, classify priority/signal,
              and select high-value meaningful findings for Groq LLM reasoning (excluding low-signal style findings).
      Phase C (Reasoning): Execute LLM reasoning for selected candidates, apply deterministic explanations
              for style/overflow findings, and assemble final ReviewIssues.
    """

    def __init__(self, review_id: str):
        self.review_id = review_id or "default"
        self.root_cause_engine = RootCauseEngine(self.review_id)
        self.tracker = get_review_tracker(self.review_id)
        self.traces: List[Dict[str, Any]] = []

    def generate(self, aggregated: Dict[str, Any]) -> List[ReviewIssue]:
        """
        Runs the deterministic finding pipeline: collect -> deduplicate -> prioritize -> select -> reason.
        """
        self.traces = []
        # PR Scope Safety Check (Requirement 8): finding.file_path ∈ PR_CHANGED_FILES
        file_path = aggregated.get("file_path", "")
        pr_changed_files = aggregated.get("pr_changed_files", [])
        if pr_changed_files:
            norm_pr_files = {DiffParser.normalize_path(p) for p in pr_changed_files if p}
            norm_fp = DiffParser.normalize_path(file_path)
            if norm_pr_files and norm_fp not in norm_pr_files:
                # File is supporting context only, never expose as reportable PR findings
                return []

        # ═══════════════════════════════════════════════════════════════
        # PHASE A — COLLECTION: Collect all raw findings from all analyzers
        # ═══════════════════════════════════════════════════════════════
        raw_findings = self._collect_all_raw_findings(aggregated)

        # Resolve file-level context
        file_path = aggregated.get("file_path", "")
        context_meta = ContextResolver.resolve(file_path)
        settings = get_settings()
        threshold = settings.REASONING_ACTIVATION_THRESHOLD
        kb_service = KnowledgeRetrievalService.get_instance()
        changed_lines_set = set(aggregated.get("changed_lines", []))

        # ─── Enrich findings with prioritization and confidence ───
        enriched_findings: List[Dict[str, Any]] = []
        for finding in raw_findings:
            line = finding.get("line", 1)
            evidence_strength = self._compute_evidence_strength(finding)
            primary_source, primary_rule, primary_msg = self._resolve_primary_source(finding)
            
            # Prioritization & low-signal tagging
            priority_info = PrioritizationEngine.analyze(
                source=primary_source,
                rule_id=primary_rule,
                message=primary_msg,
                context_meta=context_meta
            )
            
            # If finding itself was flagged as style or rule is style, enforce low-signal
            if finding.get("issue_type") == "style" or PrioritizationEngine.is_style_rule(primary_rule, primary_msg):
                priority_info["is_low_signal"] = True
                priority_info["signal_priority"] = "low"
                priority_info["issue_category"] = "style-only violations"

            is_changed = line in changed_lines_set if changed_lines_set else True
            conf_details = ConfidenceEngine.calculate(
                finding,
                finding.get("sources", []),
                finding.get("evidence", {}),
                context_meta=context_meta,
                signal_meta=priority_info,
                is_changed=is_changed
            )

            # Attach category to finding dictionary for downstream use
            finding["issue_category"] = priority_info.get("issue_category", "runtime logic risks")
            finding["confidence"] = conf_details.get("confidence", 0.8)

            enriched_findings.append({
                "line": line,
                "file_path": file_path,
                "finding": finding,
                "evidence_strength": evidence_strength,
                "primary_source": primary_source,
                "primary_rule": primary_rule,
                "primary_msg": primary_msg,
                "priority_info": priority_info,
                "conf_details": conf_details,
                "is_changed": is_changed,
            })

        # ═══════════════════════════════════════════════════════════════
        # PHASE B — DEDUPLICATION: Merge identical overlapping findings
        # ═══════════════════════════════════════════════════════════════
        deduped_findings = self._deduplicate_findings(enriched_findings)

        # ═══════════════════════════════════════════════════════════════
        # PHASE B.2 — LLM SELECTION: Rank and selectively apply LLM reasoning
        # ═══════════════════════════════════════════════════════════════
        llm_candidates, non_llm_findings = self._select_findings_for_llm(
            deduped_findings, threshold
        )

        # ═══════════════════════════════════════════════════════════════
        # PHASE C — REASONING & ASSEMBLY
        # ═══════════════════════════════════════════════════════════════
        final_issues: List[ReviewIssue] = []

        # Process LLM candidates (Groq reasoning)
        for ef in llm_candidates:
            issue = self._process_finding_with_llm(
                ef, aggregated, context_meta, kb_service, changed_lines_set, threshold
            )
            final_issues.append(issue)

        # Process non-LLM findings (deterministic static explanations)
        for ef in non_llm_findings:
            issue = self._process_finding_static(
                ef, context_meta, changed_lines_set, threshold
            )
            final_issues.append(issue)

        # Sort issues descending by priority score
        final_issues.sort(key=lambda x: x.priority_score, reverse=True)
        return final_issues

    # ═══════════════════════════════════════════════════════════════════
    # PHASE A HELPERS — Flat Finding Collection
    # ═══════════════════════════════════════════════════════════════════

    def _collect_all_raw_findings(self, aggregated: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Collect ALL raw deterministic findings from all static analyzers into a flat list, strictly PR-scoped."""
        raw_list: List[Dict[str, Any]] = []
        file_path = DiffParser.normalize_path(aggregated.get("file_path", ""))
        pr_changed_files = aggregated.get("pr_changed_files", [])
        norm_pr_files = {DiffParser.normalize_path(p) for p in pr_changed_files if p} if pr_changed_files else set()

        if norm_pr_files and file_path not in norm_pr_files:
            return []

        changed_lines_set = set(aggregated.get("changed_lines", []))

        # 1. Gather AST Mutation Detections
        mutation_analysis = aggregated.get("mutation_analysis", [])
        for item in mutation_analysis:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
            pattern = item.get("pattern", "list mutation during iteration")
            msg = item.get("message", "List mutation during iteration")
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": "high" if "shared" in pattern else "critical",
                "issue_type": "runtime_logic_error",
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "Loop" if "list" in pattern else "Class",
                        "line": line, "pattern": pattern, "message": msg,
                        "evidence_strength": 1.0
                    }],
                    "linter_rules": [], "dataflow_findings": [], "trigger_lines": [line]
                }
            })

        # 2. Gather AST Scope Tracker findings
        scope_analysis = aggregated.get("scope_analysis", [])
        for item in scope_analysis:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
            pattern = item.get("pattern", "variable_shadowing")
            msg = item.get("message", "Shadowing variable")
            strength = 0.3 if "shadow" in pattern else 0.7
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": "medium",
                "issue_type": "code_smell",
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "Assign", "line": line, "pattern": pattern,
                        "message": msg, "evidence_strength": strength
                    }],
                    "linter_rules": [], "dataflow_findings": [], "trigger_lines": [line]
                }
            })

        # 3. Gather AST Async warnings
        ast_struct = aggregated.get("ast_structural_metadata", {})
        async_issues = ast_struct.get("async_issues", []) if isinstance(ast_struct, dict) else []
        for item in async_issues:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
            pattern = item.get("type", "async_missing_await")
            msg = item.get("message", "Async issue")
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": "high",
                "issue_type": "concurrency",
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "AsyncDef/Call", "line": line, "pattern": pattern,
                        "message": msg, "evidence_strength": 0.8
                    }],
                    "linter_rules": [], "dataflow_findings": [], "trigger_lines": [line]
                }
            })

        # 3b. Gather AST Rules findings (eval_detection, exec_detection, unsafe_subprocess, unsafe_pickle, etc.)
        ast_rules_findings = ast_struct.get("ast_rules_findings", []) if isinstance(ast_struct, dict) else []
        for item in ast_rules_findings:
            line = item.get("line", 1)
            if changed_lines_set and line not in changed_lines_set:
                continue
            rule_name = item.get("rule_name", "ast_rule")
            msg = item.get("message", "AST rule match")
            strength = 1.0 if any(k in rule_name for k in ("eval", "exec", "subprocess", "pickle", "mutation")) else 0.8
            sev = "critical" if any(k in rule_name for k in ("eval", "exec", "subprocess", "pickle")) else ("high" if "mutation" in rule_name else "medium")
            issue_type = "security" if any(k in rule_name for k in ("eval", "exec", "subprocess", "pickle")) else "runtime_logic_error"
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": sev,
                "issue_type": issue_type,
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "ASTRuleNode", "line": line, "pattern": rule_name,
                        "message": msg, "evidence_strength": strength
                    }],
                    "linter_rules": [], "dataflow_findings": [], "trigger_lines": [line]
                }
            })

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
            
            # Classify issue type accurately
            if tool == "bandit" or rule.startswith("B"):
                issue_type = "security"
            elif PrioritizationEngine.is_style_rule(rule, msg):
                issue_type = "style"
            else:
                issue_type = "code_smell"

            rule_obj = {"tool": tool, "rule_id": rule, "line": line, "message": msg}
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": sev,
                "issue_type": issue_type,
                "sources": [tool],
                "evidence": {
                    "ast_nodes": [],
                    "linter_rules": [rule_obj],
                    "dataflow_findings": [],
                    "trigger_lines": [line]
                }
            })

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
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": msg,
                "severity": sev,
                "issue_type": issue_type,
                "sources": ["ast"],
                "evidence": {
                    "ast_nodes": [{
                        "node_type": "HeuristicNode", "line": line, "pattern": rule_name,
                        "message": msg, "evidence_strength": strength
                    }],
                    "linter_rules": [], "dataflow_findings": [], "trigger_lines": [line]
                }
            })

        # 6. Gather Dataflow Taint Findings
        dataflow_analysis = aggregated.get("dataflow_analysis", [])
        if isinstance(dataflow_analysis, dict):
            dataflow_analysis = dataflow_analysis.get("findings", []) or dataflow_analysis.get("taint_flows", [])
        if not isinstance(dataflow_analysis, list):
            dataflow_analysis = []
        for df in dataflow_analysis:
            if not isinstance(df, dict):
                continue
            df_file = DiffParser.normalize_path(df.get("sink_file") or df.get("file_path") or file_path)
            if norm_pr_files and df_file not in norm_pr_files:
                continue
            line = df.get("sink_line") or df.get("source_line") or 1
            if changed_lines_set and line not in changed_lines_set:
                continue
            rule_id = df.get("rule_id", "TAINT_FLOW")
            title = df.get("title", "Data Flow Taint Vulnerability")
            desc = df.get("description", "Untrusted data flows into a critical sink.")
            sev = df.get("severity", "critical").lower()
            flow_obj = {
                "rule_id": rule_id,
                "title": title,
                "source_node": df.get("source_node_id"),
                "sink_node": df.get("sink_node_id"),
                "flow_path": df.get("flow_path", []),
                "flow_path_length": df.get("flow_path_length", 0),
                "evidence_strength": 1.0,
            }
            raw_list.append({
                "line": line,
                "file_path": file_path,
                "issue": f"{title}: {desc}",
                "severity": sev,
                "issue_type": "security",
                "sources": ["dataflow"],
                "evidence": {
                    "ast_nodes": [],
                    "linter_rules": [],
                    "dataflow_findings": [flow_obj],
                    "trigger_lines": [line]
                }
            })

        # Final safety filter: guarantee finding.file_path in PR_CHANGED_FILES
        if norm_pr_files:
            raw_list = [
                f for f in raw_list
                if DiffParser.normalize_path(f.get("file_path", "")) in norm_pr_files
            ]

        return raw_list

    # ═══════════════════════════════════════════════════════════════════
    # PHASE B HELPERS — Deduplication
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _normalize_text_for_identity(text: str) -> str:
        """Normalize message text for stable identity comparisons."""
        cleaned = re.sub(r"[^\w\s]", "", str(text or "").lower())
        # Collapse whitespace
        return " ".join(cleaned.split())

    @classmethod
    def _make_finding_fingerprint(cls, ef: Dict[str, Any]) -> str:
        """Create a normalized identity fingerprint for deduplication.

        Uses file_path + line + normalized message pattern + issue_type / rule category.
        """
        finding = ef["finding"]
        file_path = ef.get("file_path", "")
        line = finding.get("line", 0)
        norm_msg = cls._normalize_text_for_identity(finding.get("issue", ""))
        issue_type = finding.get("issue_type", "").strip().lower()
        rule = ef.get("primary_rule", "").strip().lower()

        # Group common style aliases (e.g. line-too-long from flake8 vs pylint)
        if "line too long" in norm_msg or rule in ("e501", "c0301"):
            norm_msg = "line_too_long"
        elif "whitespace" in norm_msg or rule in ("w291", "w292", "w293", "c0303"):
            norm_msg = "whitespace"
        elif "missing docstring" in norm_msg or rule in ("c0114", "c0115", "c0116", "d100", "d101", "d102", "d103"):
            norm_msg = "missing_docstring"
        elif "eval" in norm_msg:
            norm_msg = "eval_call"
        elif "subprocess" in norm_msg:
            norm_msg = "subprocess_call"

        identity = f"{file_path}:{line}:{issue_type}:{norm_msg}"
        return hashlib.md5(identity.encode("utf-8", errors="replace")).hexdigest()

    def _deduplicate_findings(self, enriched_findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate overlapping findings reported by multiple analyzers on the same line.

        When merging:
        - Combine all detection sources (e.g. ["pylint", "flake8"])
        - Merge evidence AST nodes, linter rules, and dataflow findings
        - Retain the most severe rating and highest evidence strength
        """
        seen: Dict[str, Dict[str, Any]] = {}

        for ef in enriched_findings:
            fp = self._make_finding_fingerprint(ef)

            if fp not in seen:
                seen[fp] = ef
            else:
                existing = seen[fp]
                existing_finding = existing["finding"]
                new_finding = ef["finding"]

                # Merge detection sources
                for src in new_finding.get("sources", []):
                    if src not in existing_finding["sources"]:
                        existing_finding["sources"].append(src)

                # Merge evidence
                for ast_node in new_finding.get("evidence", {}).get("ast_nodes", []):
                    existing_finding["evidence"].setdefault("ast_nodes", []).append(ast_node)
                for linter_rule in new_finding.get("evidence", {}).get("linter_rules", []):
                    existing_finding["evidence"].setdefault("linter_rules", []).append(linter_rule)
                for df_finding in new_finding.get("evidence", {}).get("dataflow_findings", []):
                    existing_finding["evidence"].setdefault("dataflow_findings", []).append(df_finding)

                # Retain higher evidence strength
                if ef["evidence_strength"] > existing["evidence_strength"]:
                    existing["evidence_strength"] = ef["evidence_strength"]
                    existing["primary_rule"] = ef["primary_rule"]
                    existing["primary_msg"] = ef["primary_msg"]
                    existing["primary_source"] = ef["primary_source"]

                # Upgrade severity if new finding is more severe
                sev_order = {"info": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
                new_sev = new_finding.get("severity", "medium").lower()
                old_sev = existing_finding.get("severity", "medium").lower()
                if sev_order.get(new_sev, 0) > sev_order.get(old_sev, 0):
                    existing_finding["severity"] = new_finding["severity"]

                # Retain higher confidence
                if ef["conf_details"].get("confidence", 0) > existing["conf_details"].get("confidence", 0):
                    existing["conf_details"] = ef["conf_details"]
                    existing_finding["confidence"] = ef["conf_details"].get("confidence", 0)

        return list(seen.values())

    # ═══════════════════════════════════════════════════════════════════
    # PHASE B.2 HELPERS — Priority-Based LLM Selection
    # ═══════════════════════════════════════════════════════════════════

    def _select_findings_for_llm(
        self,
        enriched_findings: List[Dict[str, Any]],
        threshold: float
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Select and rank findings for Groq LLM reasoning.

        Returns (llm_candidates, non_llm_findings).

        Strict selection rules:
        - Low-signal style findings NEVER consume LLM budget (is_low_signal=True)
        - Finding must have evidence_strength >= threshold
        - LLM tracker budget acts as an upper bound (take at most remaining budget)

        Deterministic ranking (highest priority first):
        1. Critical severity
        2. High severity
        3. Security / Dataflow / AST dangerous pattern findings
        4. Medium severity
        5. Higher evidence strength
        6. Higher confidence
        """
        sev_rank = {"critical": 5, "high": 4, "medium": 3, "low": 2, "info": 1}
        category_rank = {
            "security": 6,
            "mutation risks": 5,
            "async misuse": 4,
            "runtime logic risks": 3,
            "maintainability insights": 2,
            "style-only violations": 1,
        }

        def _sort_key(ef: Dict[str, Any]) -> Tuple:
            finding = ef["finding"]
            priority_info = ef["priority_info"]
            severity = finding.get("severity", "medium").lower()
            has_dataflow = bool(finding.get("evidence", {}).get("dataflow_findings"))
            category = priority_info.get("issue_category", "runtime logic risks").lower()
            confidence = ef["conf_details"].get("confidence", 0.8)
            return (
                sev_rank.get(severity, 2),
                category_rank.get(category, 2),
                1 if has_dataflow else 0,
                ef["evidence_strength"],
                confidence,
            )

        llm_candidates: List[Dict[str, Any]] = []
        non_llm_findings: List[Dict[str, Any]] = []

        style_count = 0
        for ef in enriched_findings:
            priority_info = ef["priority_info"]
            is_low_signal = priority_info.get("is_low_signal", False)

            # Style findings NEVER consume LLM budget
            if is_low_signal:
                style_count += 1
                non_llm_findings.append(ef)
                continue

            # Below activation threshold -> static analysis only
            if ef["evidence_strength"] < threshold:
                non_llm_findings.append(ef)
                continue

            llm_candidates.append(ef)

        # Record accounting for skipped low-signal findings
        if style_count > 0:
            self.tracker.record_skipped_low_signal(style_count)

        # Sort LLM candidates by priority (highest priority first)
        llm_candidates.sort(key=_sort_key, reverse=True)

        # Apply budget limit: take at most budget_remaining
        budget_remaining = self.tracker.remaining_budget()
        if len(llm_candidates) > budget_remaining:
            overflow = llm_candidates[budget_remaining:]
            llm_candidates = llm_candidates[:budget_remaining]
            non_llm_findings.extend(overflow)
            self.tracker.record_skipped_budget(len(overflow))

        return llm_candidates, non_llm_findings

    # ═══════════════════════════════════════════════════════════════════
    # PHASE C HELPERS — Finding Processing
    # ═══════════════════════════════════════════════════════════════════

    def _process_finding_with_llm(
        self,
        ef: Dict[str, Any],
        aggregated: Dict[str, Any],
        context_meta: Dict[str, Any],
        kb_service: Any,
        changed_lines_set: set,
        threshold: float,
    ) -> ReviewIssue:
        """Process a single finding through Groq LLM reasoning."""
        line = ef["line"]
        finding = ef["finding"]
        evidence_strength = ef["evidence_strength"]
        primary_source = ef["primary_source"]
        primary_rule = ef["primary_rule"]
        primary_msg = ef["primary_msg"]
        priority_info = ef["priority_info"]
        conf_details = ef["conf_details"]
        is_changed = ef["is_changed"]

        # A: Retrieve RAG Knowledge
        try:
            assembled_knowledge = kb_service.retrieve_for_finding(
                finding=finding,
                repo_context=aggregated.get("repository_intelligence", {}),
                top_k=2,
            )
            knowledge_context_str = assembled_knowledge.formatted_prompt_context
            knowledge_sources = assembled_knowledge.sources
        except Exception:
            knowledge_context_str = ""
            knowledge_sources = []

        # B: Attempt LLM reasoning
        can_use_llm = (
            self.tracker.can_request()
            and not self.tracker.degraded_mode
        )

        reasoning_source = "static_analysis"
        reasoning_activated = False
        ai_details = None

        if can_use_llm:
            enriched_aggregated = dict(aggregated)
            if knowledge_context_str and knowledge_context_str != "No relevant context found.":
                enriched_aggregated["retrieved_knowledge"] = knowledge_context_str
            ai_details = self.root_cause_engine.analyze_finding(finding, enriched_aggregated)
            if (
                ai_details
                and ai_details.get("reasoning_source") != "static_analysis"
                and (ai_details.get("root_cause") or ai_details.get("fix"))
            ):
                reasoning_source = "llm"
                reasoning_activated = True
            else:
                # LLM returned or failed -> fallback to deterministic explanation
                if not ai_details or ai_details.get("reasoning_source") == "static_analysis":
                    ai_details = self._generate_static_explanation(finding, primary_rule, primary_msg)
                reasoning_source = "static_analysis"
                reasoning_activated = False
        else:
            ai_details = self._generate_static_explanation(finding, primary_rule, primary_msg)

        return self._build_review_issue(
            line, finding, evidence_strength, primary_source, primary_rule, primary_msg,
            priority_info, conf_details, is_changed, ai_details, reasoning_source,
            reasoning_activated, knowledge_sources, changed_lines_set, threshold,
            file_path=ef.get("file_path")
        )

    def _process_finding_static(
        self,
        ef: Dict[str, Any],
        context_meta: Dict[str, Any],
        changed_lines_set: set,
        threshold: float,
    ) -> ReviewIssue:
        """Process a finding with deterministic static-only explanation (no LLM call)."""
        line = ef["line"]
        finding = ef["finding"]
        evidence_strength = ef["evidence_strength"]
        primary_source = ef["primary_source"]
        primary_rule = ef["primary_rule"]
        primary_msg = ef["primary_msg"]
        priority_info = ef["priority_info"]
        conf_details = ef["conf_details"]
        is_changed = ef["is_changed"]

        ai_details = self._generate_static_explanation(finding, primary_rule, primary_msg)
        reasoning_source = "static_analysis"
        reasoning_activated = False

        return self._build_review_issue(
            line, finding, evidence_strength, primary_source, primary_rule, primary_msg,
            priority_info, conf_details, is_changed, ai_details, reasoning_source,
            reasoning_activated, [], changed_lines_set, threshold,
            file_path=ef.get("file_path")
        )

    def _build_review_issue(
        self,
        line: int,
        finding: Dict[str, Any],
        evidence_strength: float,
        primary_source: str,
        primary_rule: str,
        primary_msg: str,
        priority_info: Dict[str, Any],
        conf_details: Dict[str, Any],
        is_changed: bool,
        ai_details: Dict[str, Any],
        reasoning_source: str,
        reasoning_activated: bool,
        knowledge_sources: List[str],
        changed_lines_set: set,
        threshold: float,
        file_path: Optional[str] = None,
    ) -> ReviewIssue:
        """Build a ReviewIssue from all computed data."""
        # Priority score calculation
        sev = priority_info.get("signal_priority", finding["severity"]).lower()
        sev_weights = {"critical": 1.0, "high": 0.8, "medium": 0.5, "low": 0.2, "info": 0.1}
        severity_weight = sev_weights.get(sev, 0.5)

        cat = priority_info.get("issue_category", "runtime logic risks").lower()
        cat_weights = {
            "security": 1.0, "mutation risks": 0.9, "async misuse": 0.85,
            "runtime logic risks": 0.75, "maintainability insights": 0.4, "style-only violations": 0.2
        }
        category_weight = cat_weights.get(cat, 0.5)

        raw_priority = (
            severity_weight * 0.40
            + category_weight * 0.30
            + evidence_strength * 0.20
            + (1.0 if is_changed else 0.5) * 0.10
        )
        priority_score = round(min(1.0, max(0.0, raw_priority)), 2)

        # Reasoning traces
        reasoning_trace = [
            f"Rule '{primary_rule}' from {primary_source} evaluated with evidence strength {evidence_strength:.2f}.",
            f"Confidence {conf_details['confidence']:.2f} calibrated from {len(conf_details['reasons'])} factors.",
            f"Priority score {priority_score:.2f} based on {sev} severity and category '{cat}'.",
        ]
        llm_provider = ai_details.get("llm_provider") if reasoning_activated else None
        llm_model = ai_details.get("llm_model") if reasoning_activated else None

        if reasoning_activated:
            p_display = (llm_provider or "Groq").capitalize()
            m_display = f" ({llm_model})" if llm_model and llm_model != "unknown" else ""
            reasoning_trace.append(f"Root cause reasoned with {p_display} LLM{m_display}.")
        else:
            reasoning_trace.append("Static rule explanation applied (Bypassed LLM reasoning).")

        # Extract dataflow path if available
        evidence_dict = finding.get("evidence", {}) or {}
        df_findings = evidence_dict.get("dataflow_findings", [])
        dataflow_path = None
        if df_findings and isinstance(df_findings, list):
            first_df = df_findings[0]
            if isinstance(first_df, dict) and first_df.get("flow_path"):
                dataflow_path = [str(p) for p in first_df["flow_path"]]

        # Ensure all detection sources are preserved
        detection_sources = list(finding.get("sources", []))
        if primary_source and primary_source not in detection_sources:
            detection_sources.append(primary_source)
        if df_findings and "dataflow" not in detection_sources:
            detection_sources.append("dataflow")
        if not detection_sources:
            detection_sources = ["ast"]

        # Extract or derive standards
        standards = list(finding.get("standards") or [])
        iss_text = (finding.get("issue") or "").lower()
        if not standards:
            if "sql" in iss_text:
                standards = ["CWE-89", "OWASP A03:2021-Injection"]
            elif "command" in iss_text or "shell" in iss_text:
                standards = ["CWE-78", "OWASP A03:2021-Injection"]
            elif "xss" in iss_text:
                standards = ["CWE-79", "OWASP A03:2021-Injection"]
            elif "path" in iss_text or "traversal" in iss_text:
                standards = ["CWE-22", "OWASP A01:2021-Broken Access Control"]
            elif "pickle" in iss_text or "deserial" in iss_text:
                standards = ["CWE-502", "OWASP A08:2021-Software and Data Integrity Failures"]
            elif finding.get("severity") in ("critical", "high"):
                standards = ["CWE-Security", "OWASP ASVS"]

        # Extract impact
        impact = ai_details.get("impact")
        if not impact:
            sev = finding.get("severity", "medium").lower()
            if sev == "critical":
                impact = "Potential remote code execution, database compromise, or severe unauthorized system access."
            elif sev == "high":
                impact = "Unvalidated input propagation could alter control flow or sensitive state integrity."
            else:
                impact = "Defensive coding or maintainability standard violation."

        # Record confidence_and_grounding trace for observability and verification
        self.traces.append({
            "stage": "confidence_and_grounding",
            "duration_ms": 0.0,
            "input_data": {
                "line": line,
                "sources": detection_sources,
                "evidence": finding.get("evidence", {}),
            },
            "output_data": {
                "arithmetic_steps": reasoning_trace,
                "confidence_score": conf_details["confidence"],
                "evidence_strength": evidence_strength,
                "reasoning_activated": reasoning_activated,
                "priority_score": priority_score,
                "source_attributions": {
                    "linters": [r.get("tool") for r in finding.get("evidence", {}).get("linter_rules", [])],
                    "ast_patterns": [n.get("pattern", n.get("rule_name", "")) for n in finding.get("evidence", {}).get("ast_nodes", [])],
                    "dataflow_findings": [f.get("rule_id") for f in finding.get("evidence", {}).get("dataflow_findings", [])],
                },
            },
        })

        return ReviewIssue(
            line=line,
            file_path=file_path or finding.get("file_path"),
            severity=finding.get("severity", "medium"),
            confidence=conf_details["confidence"],
            issue=finding.get("issue", ""),
            root_cause=ai_details.get("root_cause") or "",
            trigger_condition=ai_details.get("trigger_condition") or "",
            fix=ai_details.get("fix") or "",
            patch=ai_details.get("patch", ""),
            issue_type=ai_details.get("issue_type", finding.get("issue_type", "code_smell")),
            sources=detection_sources,
            reasoning_trace=reasoning_trace,
            evidence=finding.get("evidence", {}),
            signal_priority=priority_info.get("signal_priority", "medium"),
            issue_category=priority_info.get("issue_category", "runtime logic risks"),
            is_low_signal=priority_info.get("is_low_signal", False),
            detection_source=primary_source,
            reasoning_source=reasoning_source,
            priority_score=priority_score,
            detection_sources=detection_sources,
            llm_provider=llm_provider,
            llm_model=llm_model,
            dataflow_path=dataflow_path,
            standards=standards,
            impact=impact,
            category=priority_info.get("issue_category", "runtime logic risks"),
        )

    # ═══════════════════════════════════════════════════════════════════
    # EVIDENCE & EXPLANATION HELPERS
    # ═══════════════════════════════════════════════════════════════════

    @staticmethod
    def _compute_evidence_strength(finding: Dict[str, Any]) -> float:
        """Compute aggregated evidence strength from all detector signals."""
        evidence = finding.get("evidence", {})
        strengths = []
        for node in evidence.get("ast_nodes", []):
            strengths.append(node.get("evidence_strength", 0.5))
        for df in evidence.get("dataflow_findings", []):
            strengths.append(df.get("evidence_strength", 1.0))
        for rule in evidence.get("linter_rules", []):
            strengths.append(0.6)
        if strengths:
            return round(max(strengths), 2)
        return 0.5

    @staticmethod
    def _resolve_primary_source(finding: Dict[str, Any]) -> Tuple[str, str, str]:
        """Determine the primary detector, rule ID, and message for a finding."""
        sources = finding.get("sources", [])
        evidence = finding.get("evidence", {})

        # Priority 1: Dataflow / Taint
        if "dataflow" in sources and evidence.get("dataflow_findings"):
            df = evidence["dataflow_findings"][0]
            return "dataflow", df.get("rule_id", "TAINT_FLOW"), df.get("title", "Data Flow Taint")

        # Priority 2: Security Linters (Bandit)
        for rule in evidence.get("linter_rules", []):
            if rule.get("tool") == "bandit":
                return "bandit", rule.get("rule_id", "SECURITY"), rule.get("message", "")

        # Priority 3: AST Rules / Detections
        if "ast" in sources and evidence.get("ast_nodes"):
            node = evidence["ast_nodes"][0]
            return "ast", node.get("pattern", "ast_detection"), node.get("message", "")

        # Priority 4: Other Linters
        if evidence.get("linter_rules"):
            rule = evidence["linter_rules"][0]
            return rule.get("tool", "linter"), rule.get("rule_id", ""), rule.get("message", "")

        return sources[0] if sources else "ast", "generic_rule", finding.get("issue", "")

    @staticmethod
    def _generate_static_explanation(finding: Dict[str, Any], rule_id: str, message: str) -> Dict[str, Any]:
        """Generate a deterministic explanation when LLM reasoning is not used or unavailable."""
        issue_text = finding.get("issue", message or "Code quality issue detected.")
        issue_type = finding.get("issue_type", "code_smell")

        # Contextual templates based on rule and issue type
        if "eval" in rule_id.lower() or "eval" in issue_text.lower():
            return {
                "root_cause": "Static analysis detected potential hazardous behavior: dynamic code execution via eval() allows arbitrary code execution if input is untrusted.",
                "trigger_condition": "Triggers whenever this code path receives externally influenced or untrusted strings.",
                "fix": "Replace eval() with safe alternatives like ast.literal_eval() or dedicated parsers.",
                "patch": "",
                "issue_type": "security",
                "reasoning_source": "static_analysis"
            }
        elif "subprocess" in rule_id.lower() or "shell" in issue_text.lower():
            return {
                "root_cause": "Invoking system commands through shell execution exposes the application to command injection.",
                "trigger_condition": "Triggers when unsanitized arguments are passed to the subprocess call.",
                "fix": "Pass command arguments as a list with shell=False, or use shlex.quote() for input sanitization.",
                "patch": "",
                "issue_type": "security",
                "reasoning_source": "static_analysis"
            }
        elif "mutation" in rule_id.lower() or "mutation" in issue_text.lower():
            return {
                "root_cause": "Modifying a collection while iterating over it causes index shifts and skipped elements.",
                "trigger_condition": "Triggers during iteration when items are added or removed from the collection.",
                "fix": "Iterate over a copy of the collection using list(collection) or construct a new filtered collection.",
                "patch": "",
                "issue_type": "runtime_logic_error",
                "reasoning_source": "static_analysis"
            }
        elif "shadow" in rule_id.lower() or "shadow" in issue_text.lower():
            return {
                "root_cause": "Local variable name shadows an outer-scope variable or built-in identifier.",
                "trigger_condition": "Triggers during reference resolution, obscuring access to the outer symbol.",
                "fix": "Rename the local variable to use a distinct, descriptive identifier.",
                "patch": "",
                "issue_type": "code_smell",
                "reasoning_source": "static_analysis"
            }
        elif PrioritizationEngine.is_style_rule(rule_id, message):
            return {
                "root_cause": f"Code formatting violation: {issue_text}.",
                "trigger_condition": "Static style violation detected during linting inspection.",
                "fix": "Reformat the line according to standard PEP 8 formatting conventions.",
                "patch": "",
                "issue_type": "style",
                "reasoning_source": "static_analysis"
            }

        return {
            "root_cause": f"Static analysis identified: {issue_text}.",
            "trigger_condition": "Detected during static code inspection.",
            "fix": "Review the highlighted line and refactor according to project coding standards.",
            "patch": "",
            "issue_type": issue_type,
            "reasoning_source": "static_analysis"
        }
