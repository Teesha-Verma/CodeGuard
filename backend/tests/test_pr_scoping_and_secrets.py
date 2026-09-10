"""
Comprehensive test suite verifying:
1. Exact PR-scoped analysis (no suffix/basename/fuzzy expansion).
2. Same-basename isolation (e.g., src/utils/parser.py vs tests/utils/parser.py vs legacy/parser.py).
3. Multiple changed files.
4. Supporting context scope (cross-file imports provide context, but findings in supporting files are not PR findings).
5. Removed file handling (deleted files are skipped from active AST analysis).
6. Renamed file handling (new path analyzed, old path skipped).
7. Style findings strictly PR-scoped.
8. LLM context boundedness (no whole-repo dumps).
9. Git ignore protection (.env ignored, .env.example tracked).
10. Secret-safe logging and error response sanitization.
"""

import json
import logging
import os
import tempfile
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.analysis.repository.supporting_context import PRSupportingContextProvider
from app.api.schemas import FileReport
from app.core.logger import mask_secrets, JSONFormatter
from app.diff.diff_parser import DiffFile, DiffHunk, ChangedLine, DiffParser
from app.github.github_client import GitHubClient, PRFileEntry
from app.pipeline.orchestrator import PipelineOrchestrator
from app.pipeline.runner import run_pr_review_task
from app.reasoning.review_generator import ReviewGenerator, ReviewIssue
from app.reasoning.root_cause_engine import RootCauseEngine


# ============================================================================
# 1. PATH NORMALIZATION & EXACT PR FILE SCOPE
# ============================================================================

def test_diff_parser_path_normalization():
    """Verify DiffParser normalizes paths removing git prefixes a/, b/, ./ and slashes."""
    assert DiffParser.normalize_path("a/src/utils/parser.py") == "src/utils/parser.py"
    assert DiffParser.normalize_path("b/src/utils/parser.py") == "src/utils/parser.py"
    assert DiffParser.normalize_path("./src/utils/parser.py") == "src/utils/parser.py"
    assert DiffParser.normalize_path("src\\utils\\parser.py") == "src/utils/parser.py"
    assert DiffParser.normalize_path("/src/utils/parser.py") == "src/utils/parser.py"


def test_exact_pr_scope_excludes_same_basename():
    """
    Test requirement 21:
    Repository contains:
      - src/utils/parser.py
      - tests/utils/parser.py
      - legacy/parser.py
    PR changes:
      - src/utils/parser.py
    Expected:
      Primary analysis is strictly src/utils/parser.py, NOT tests/utils/parser.py or legacy/parser.py.
    """
    pr_changed_files = ["src/utils/parser.py"]
    provider = PRSupportingContextProvider(pr_changed_files=pr_changed_files)

    # All candidate files in repo
    all_repo_files = [
        "src/utils/parser.py",
        "tests/utils/parser.py",
        "legacy/parser.py",
        "src/other.py",
    ]

    primary = provider.filter_primary_files(all_repo_files)
    assert primary == ["src/utils/parser.py"]
    assert "tests/utils/parser.py" not in primary
    assert "legacy/parser.py" not in primary


def test_multiple_changed_files_exact_scoping():
    """
    Test requirement 22:
    PR changes:
      - src/a.py
      - src/b.py
      - src/security/c.py
    Only these exact paths are primary targets.
    """
    pr_changed_files = ["src/a.py", "src/b.py", "src/security/c.py"]
    provider = PRSupportingContextProvider(pr_changed_files=pr_changed_files)

    candidate_files = [
        "src/a.py",
        "tests/a.py",
        "src/b.py",
        "legacy/b.py",
        "src/security/c.py",
        "tests/security/c.py",
        "src/d.py",
    ]

    primary = provider.filter_primary_files(candidate_files)
    assert set(primary) == {"src/a.py", "src/b.py", "src/security/c.py"}


# ============================================================================
# 2. FILE STATUSES: ADDED, MODIFIED, RENAMED, REMOVED
# ============================================================================

def test_github_client_file_status_filtering():
    """Verify removed files are excluded from active analysis while added/modified/renamed are included."""
    mock_response = [
        {"filename": "src/added.py", "status": "added", "patch": "@@ -0,0 +1 @@\n+x = 1"},
        {"filename": "src/modified.py", "status": "modified", "patch": "@@ -1 +1 @@\n-x = 1\n+x = 2"},
        {"filename": "src/renamed_new.py", "status": "renamed", "previous_filename": "src/renamed_old.py", "patch": "@@ -1 +1 @@\n-x = 1\n+x = 2"},
        {"filename": "src/deleted.py", "status": "removed", "patch": "@@ -1 +0,0 @@\n-x = 1"},
    ]

    client = GitHubClient(token="mock-token")
    with patch.object(client, "get_pull_request_files", return_value=mock_response):
        entries = client.get_pr_file_entries("owner", "repo", 1)
        assert len(entries) == 4
        
        # Test default include_removed=False
        active_files = client.get_pr_changed_files("owner", "repo", 1, include_removed=False)
        assert active_files == ["src/added.py", "src/modified.py", "src/renamed_new.py"]
        assert "src/deleted.py" not in active_files

        # Test include_removed=True
        all_files = client.get_pr_changed_files("owner", "repo", 1, include_removed=True)
        assert "src/deleted.py" in all_files


def test_diff_parser_renamed_and_deleted():
    """Verify DiffParser accurately detects renamed and deleted files from patches."""
    deleted_patch = """diff --git a/src/old.py b/src/old.py
deleted file mode 100644
index 1234567..0000000
--- a/src/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-def old():
-    pass
"""
    files = DiffParser.parse(deleted_patch)
    assert len(files) == 1
    assert files[0].is_deleted is True
    assert files[0].file_path == "src/old.py"

    renamed_patch = """diff --git a/src/before.py b/src/after.py
similarity index 95%
rename from src/before.py
rename to src/after.py
index 1234567..89abcdef
--- a/src/before.py
+++ b/src/after.py
@@ -1,2 +1,2 @@
-def foo():
+def foo_updated():
     pass
"""
    files = DiffParser.parse(renamed_patch)
    assert len(files) == 1
    assert files[0].is_rename is True
    assert files[0].old_file_path == "src/before.py"
    assert files[0].file_path == "src/after.py"


# ============================================================================
# 3. SUPPORTING CONTEXT RESOLUTION & ISOLATION
# ============================================================================

def test_supporting_context_extracts_imports_only():
    """
    Test requirement 23:
    src/api.py imports src/services/auth.py.
    Supporting context loads auth.py to resolve symbols, but does not add unrelated files.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        api_dir = os.path.join(temp_dir, "src")
        services_dir = os.path.join(temp_dir, "src", "services")
        os.makedirs(services_dir, exist_ok=True)

        api_file = os.path.join(api_dir, "api.py")
        with open(api_file, "w", encoding="utf-8") as f:
            f.write("from src.services.auth import authenticate\ndef handle(token):\n    return authenticate(token)\n")

        auth_file = os.path.join(services_dir, "auth.py")
        with open(auth_file, "w", encoding="utf-8") as f:
            f.write("def authenticate(token):\n    # Eval is dangerous\n    eval(token)\n")

        unrelated_file = os.path.join(temp_dir, "src", "unrelated.py")
        with open(unrelated_file, "w", encoding="utf-8") as f:
            f.write("def do_something_else():\n    pass\n")

        provider = PRSupportingContextProvider(
            pr_changed_files=["src/api.py"],
            repo_path=temp_dir
        )
        ctx = provider.build_supporting_context()

        # Primary is only src/api.py
        assert ctx.primary_files == ["src/api.py"]

        # auth.py should be identified as supporting file because of the import
        assert any("auth.py" in p for p in ctx.supporting_files)
        # unrelated.py should NOT be identified as supporting file
        assert not any("unrelated.py" in p for p in ctx.supporting_files)


def test_review_generator_drops_findings_outside_pr_scope():
    """
    Test requirement 8:
    Verify that ReviewGenerator strictly drops any findings where finding.file_path is not in pr_changed_files.
    """
    rg = ReviewGenerator(review_id="test_pr_drops")

    # Primary PR file features -> should produce review issues
    features_pr = {
        "file_path": "src/api.py",
        "changed_lines": [10],
        "ast_structural_metadata": {
            "ast_rules_findings": [
                {
                    "line": 10,
                    "rule_name": "eval_detection",
                    "message": "Dangerous eval call in PR file"
                }
            ]
        },
        "pr_changed_files": ["src/api.py"],
    }
    issues_pr = rg.generate(features_pr)
    assert len(issues_pr) == 1
    assert issues_pr[0].file_path == "src/api.py"

    # Supporting context file (e.g. auth.py, NOT in pr_changed_files) -> must produce ZERO issues
    features_supporting = {
        "file_path": "src/services/auth.py",
        "changed_lines": [5],
        "ast_structural_metadata": {
            "ast_rules_findings": [
                {
                    "line": 5,
                    "rule_name": "eval_detection",
                    "message": "Dangerous eval call in supporting file"
                }
            ]
        },
        "pr_changed_files": ["src/api.py"],  # auth.py is NOT in pr_changed_files
    }
    issues_supporting = rg.generate(features_supporting)
    assert len(issues_supporting) == 0


def test_style_findings_strictly_pr_scoped():
    """
    Test requirement 16 & 26:
    Style findings (Flake8 E501, W293) on unrelated repository files are never included.
    """
    rg = ReviewGenerator(review_id="test_style_scope")
    features = {
        "raw_findings": [
            {
                "file_path": "unrelated/legacy.py",
                "line": 1,
                "rule_id": "E501",
                "message": "Line too long",
                "severity": "info",
                "confidence": 0.9,
                "category": "style",
            }
        ],
        "ast_issues": [],
        "linter_issues": [],
        "complexity_issues": [],
        "call_graph_issues": [],
        "dataflow_issues": [],
        "file_path": "src/clean_feature.py",
        "pr_changed_files": ["src/clean_feature.py"],
    }

    issues = rg.generate(features)

    assert len(issues) == 0


# ============================================================================
# 4. PIPELINE RUNNER PR SCOPING & METRICS
# ============================================================================

def test_run_pr_review_task_pr_scoping(tmp_path):
    """
    Verify run_pr_review_task analyzes ONLY PR files, avoids full-repo scans,
    and sets files_analyzed correctly.
    """
    review_id = "test_pr_review_scope_123"
    repo_dir = tmp_path / review_id
    src_dir = repo_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)

    main_py = src_dir / "main.py"
    main_py.write_text("def run():\n    eval('dangerous')\n", encoding="utf-8")

    unrelated_py = src_dir / "unrelated.py"
    unrelated_py.write_text("def safe():\n    pass\n", encoding="utf-8")

    diff_text = """diff --git a/src/main.py b/src/main.py
index 0000000..1111111 100644
--- a/src/main.py
+++ b/src/main.py
@@ -1,3 +1,3 @@
 def run():
-    pass
+    eval('dangerous')
"""

    mock_client = MagicMock()
    mock_client.get_pull_request.return_value = {
        "base": {"ref": "main", "repo": {"clone_url": "https://github.com/example/repo"}}
    }
    mock_client.get_pr_changed_files.return_value = ["src/main.py"]
    mock_client.clone_and_checkout_pr.return_value = {
        "diff_text": diff_text,
        "base_ref": "main",
        "target_dir": str(repo_dir),
    }

    mock_file_report = FileReport(
        file_path="src/main.py",
        meaningful_issues=[],
        style_findings=[],
        suppressed_findings=[],
        total_issues=0
    )

    with patch("app.github.GitHubClient", return_value=mock_client), \
         patch("app.pipeline.runner.get_settings") as mock_settings, \
         patch("app.pipeline.runner._update_review_status_in_db"), \
         patch("app.pipeline.runner._save_review_results_to_db"), \
         patch("app.pipeline.runner.PipelineOrchestrator.process_file", return_value=mock_file_report) as mock_process, \
         patch("app.pipeline.runner.ReviewStore.save_report") as mock_save_report:

        settings_obj = MagicMock()
        settings_obj.REPOS_DIR = str(tmp_path)
        settings_obj.MAX_REVIEW_DURATION_SECONDS = 300
        mock_settings.return_value = settings_obj

        run_pr_review_task(
            review_id=review_id,
            repo_url="https://github.com/example/repo",
            pr_number=42
        )

        # Process called ONLY for src/main.py, NOT unrelated.py
        assert mock_process.call_count == 1
        call_diff_file = mock_process.call_args.kwargs.get("diff_file")
        assert call_diff_file is not None
        assert call_diff_file.file_path == "src/main.py"

        # Check saved report
        assert mock_save_report.call_count == 1
        saved_report = mock_save_report.call_args[0][0]
        assert saved_report.summary_stats["files_analyzed"] == 1
        assert "supporting_files_used" in saved_report.summary_stats


def test_llm_reasoning_context_bounds():
    """
    Test requirement 27:
    Verify that RootCauseEngine LLM calls include only localized context (target line ± window)
    and do not send unrelated repository files.
    """
    engine = RootCauseEngine(review_id="test_review_bounds")

    code_lines = [f"line_{i} = {i}" for i in range(1, 201)]
    code_lines[99] = "eval(user_input)"  # line 100
    code = "\n".join(code_lines)

    finding = {
        "line": 100,
        "issue": "Use of dangerous function eval",
        "issue_type": "security",
        "severity": "critical"
    }

    aggregated_context = {
        "file_path": "src/api/auth.py",
        "full_code": code,
        "ast_structural_metadata": {
            "functions": [],
            "control_structures": [],
            "ast_rules_findings": []
        }
    }

    with patch.object(engine.llm_client, "generate_structured", return_value={"root_cause": "Why", "trigger_condition": "When", "fix": "How", "patch": "", "issue_type": "security"}) as mock_generate:
        engine.analyze_finding(finding, aggregated_context)

        assert mock_generate.call_count == 1
        system_prompt, user_content = mock_generate.call_args[0]
        payload = json.loads(user_content)

        localized_code = payload["localized_source_context"]

        # Localized code must contain line 100
        assert "eval(user_input)" in localized_code
        # Localized code must NOT contain distant lines like line 1 or line 200 (bounded to ±50 lines)
        assert "line_1 = 1" not in localized_code
        assert "line_200 = 200" not in localized_code


# ============================================================================
# 5. SECRET PROTECTION & GITIGNORE HARDENING
# ============================================================================

def test_gitignore_ignores_env_files():
    """
    Verify .gitignore patterns match .env, .env.local, .env.production,
    but NOT .env.example.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    root_gitignore = os.path.join(root_dir, ".gitignore")
    backend_gitignore = os.path.join(root_dir, "backend", ".gitignore")

    assert os.path.exists(root_gitignore), "Root .gitignore must exist"
    assert os.path.exists(backend_gitignore), "Backend .gitignore must exist"

    with open(backend_gitignore, "r", encoding="utf-8") as f:
        backend_lines = f.read()

    assert ".env" in backend_lines
    assert "!.env.example" in backend_lines
    assert "*.pem" in backend_lines
    assert "*.key" in backend_lines


def test_env_example_has_no_secrets():
    """
    Verify backend/.env.example contains only placeholders, not real API keys.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env_example = os.path.join(root_dir, "backend", ".env.example")
    assert os.path.exists(env_example), "backend/.env.example must exist"

    with open(env_example, "r", encoding="utf-8") as f:
        content = f.read()

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            # Keys like GROQ_API_KEY, GEMINI_API_KEY, GITHUB_TOKEN must be empty in example
            if any(k in key for k in ["API_KEY", "GITHUB_TOKEN", "AUTH_TOKEN", "PASSWORD", "SECRET"]):
                assert val == "" or val.startswith("your_") or val.startswith("placeholder"), (
                    f"Found potential real credential in .env.example: {key}={val}"
                )


def test_secret_masking_in_logger():
    """
    Test requirement 36:
    Ensure mask_secrets redacts sensitive keys, tokens, bearer headers, and passwords.
    """
    raw_message = (
        "Calling Groq with gsk_abcdef1234567890abcdef1234567890\n"
        "Calling Gemini with AIzaSyD1234567890abcdef1234567890\n"
        "GitHub token ghp_1234567890abcdef1234567890abcdef12\n"
        "Authorization: Bearer my_secret_jwt_token_123\n"
        "DB URL: postgresql://admin:SuperSecretPass123@localhost:5432/mydb"
    )

    masked = mask_secrets(raw_message)

    assert "gsk_abcdef1234567890" not in masked
    assert "gsk_***REDACTED***" in masked

    assert "AIzaSyD1234567890" not in masked
    assert "AIzaSy***REDACTED***" in masked

    assert "ghp_1234567890" not in masked
    assert "ghp_***REDACTED***" in masked

    assert "my_secret_jwt_token_123" not in masked
    assert "Bearer ***REDACTED***" in masked

    assert "SuperSecretPass123" not in masked
    assert "***REDACTED***" in masked


def test_json_formatter_masks_secrets():
    """Ensure JSONFormatter automatically sanitizes logs."""
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="Connected to postgresql://user:SecretPass1@db.host/prod with key gsk_1234567890abcdef1234567890",
        args=(),
        exc_info=None
    )

    formatted = formatter.format(record)
    log_json = json.loads(formatted)

    assert "SecretPass1" not in log_json["message"]
    assert "gsk_1234567890" not in log_json["message"]
    assert "gsk_***REDACTED***" in log_json["message"]
    assert "***REDACTED***" in log_json["message"]
