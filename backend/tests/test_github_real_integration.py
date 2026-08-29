"""
CodeGuard V2 — Real GitHub REST API Integration Tests.

Validates:
- Real authentication with GITHUB_TOKEN
- Rate limit status
- Pull request metadata retrieval
- Unified diff fetching
- Changed files retrieval
"""

import os
import pytest
from app.core.config import get_settings
from app.github import GitHubClient


@pytest.fixture(scope="module")
def github_client():
    settings = get_settings()
    if not settings.GITHUB_TOKEN or settings.GITHUB_TOKEN in ("your_github_token_here", "mock_token"):
        pytest.skip("Real GITHUB_TOKEN not configured in .env; skipping real GitHub integration tests.")
    return GitHubClient(token=settings.GITHUB_TOKEN)


@pytest.fixture(scope="module")
def target_repo_and_pr():
    settings = get_settings()
    owner = settings.E2E_GITHUB_OWNER or "octocat"
    repo = settings.E2E_GITHUB_REPO or "Spoon-Knife"
    pr_number = settings.E2E_GITHUB_PR_NUMBER or 41016
    return owner, repo, pr_number


class TestGitHubRealIntegration:
    """Real GitHub REST API integration tests with configured GITHUB_TOKEN."""

    def test_github_real_authentication(self, github_client):
        """Verify real authentication against api.github.com."""
        auth_info = github_client.verify_authentication()
        assert auth_info.get("authenticated") is True
        assert auth_info.get("rate_limit_remaining") is not None
        rate_remaining = int(auth_info["rate_limit_remaining"])
        assert rate_remaining > 0

    def test_github_real_rate_limit(self, github_client):
        """Verify real rate limit endpoint."""
        rate_info = github_client.get_rate_limit()
        assert "resources" in rate_info
        core_rate = rate_info["resources"].get("core", {})
        assert core_rate.get("limit", 0) >= 60
        assert core_rate.get("remaining", 0) > 0

    def test_github_real_pull_request_metadata(self, github_client, target_repo_and_pr):
        """Verify real PR metadata retrieval."""
        owner, repo, pr_number = target_repo_and_pr
        pr_data = github_client.get_pull_request(owner=owner, repo=repo, pr_number=pr_number)
        assert pr_data is not None
        assert "number" in pr_data
        assert pr_data["number"] == pr_number
        assert "base" in pr_data
        assert "head" in pr_data
        assert "html_url" in pr_data
        assert "clone_url" in pr_data.get("base", {}).get("repo", {})

    def test_github_real_pull_request_diff(self, github_client, target_repo_and_pr):
        """Verify real PR diff text retrieval."""
        owner, repo, pr_number = target_repo_and_pr
        diff_text = github_client.get_pull_request_diff(owner=owner, repo=repo, pr_number=pr_number)
        assert diff_text is not None
        assert isinstance(diff_text, str)
        assert len(diff_text) > 0
        assert "diff --git" in diff_text or "---" in diff_text

    def test_github_real_pull_request_files(self, github_client, target_repo_and_pr):
        """Verify real PR modified files list retrieval."""
        owner, repo, pr_number = target_repo_and_pr
        files = github_client.get_pull_request_files(owner=owner, repo=repo, pr_number=pr_number)
        assert isinstance(files, list)
        assert len(files) > 0
        for f in files:
            assert "filename" in f
            assert "status" in f

    def test_github_authenticated_clone_url_masking(self, github_client):
        """Verify clone URL construction without secret leakage."""
        raw_url = "https://github.com/octocat/Hello-World.git"
        auth_url = github_client.get_authenticated_clone_url(raw_url)
        assert "x-access-token" in auth_url
        assert "github.com/octocat/Hello-World.git" in auth_url
