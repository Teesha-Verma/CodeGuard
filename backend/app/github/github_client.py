"""
CodeGuard V2 — GitHub REST API Client.

Handles authenticated GitHub API interactions:
- PR metadata retrieval
- Unified diff fetching
- Changed files analysis
- Authenticated repository cloning and checkout
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import get_settings

logger = logging.getLogger("codeguard.github")


class GitHubClient:
    """Production GitHub REST API Client for CodeGuard PR review workflows."""

    def __init__(
        self,
        token: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        settings = get_settings()
        self.token = token if token is not None else settings.GITHUB_TOKEN
        self.api_url = (api_url or settings.GITHUB_API_URL or "https://api.github.com").rstrip("/")
        self.timeout = timeout if timeout is not None else settings.GITHUB_TIMEOUT or 30

    def _get_headers(self, accept: str = "application/vnd.github.v3+json") -> Dict[str, str]:
        """Build request headers with optional Bearer/token authorization."""
        headers = {
            "Accept": accept,
            "User-Agent": "CodeGuard-ReviewEngine",
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def verify_authentication(self) -> Dict[str, Any]:
        """
        Verify GitHub token authentication and rate limit availability.
        Returns user info if user-scoped, or rate limit info.
        """
        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.api_url}/user", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "authenticated": True,
                    "login": data.get("login", ""),
                    "rate_limit_remaining": resp.headers.get("x-ratelimit-remaining"),
                }
            elif resp.status_code == 401:
                raise ValueError("GitHub authentication failed: Bad credentials.")
            elif resp.status_code == 403:
                # Could be fine-grained token without user profile scope, check rate_limit
                rl_resp = client.get(f"{self.api_url}/rate_limit", headers=headers)
                if rl_resp.status_code == 200:
                    return {
                        "authenticated": True,
                        "login": "token_authenticated",
                        "rate_limit_remaining": rl_resp.headers.get("x-ratelimit-remaining"),
                    }
                raise PermissionError("GitHub API rate limit exceeded or access forbidden.")
            else:
                resp.raise_for_status()
                return {"authenticated": False}

    def get_rate_limit(self) -> Dict[str, Any]:
        """Retrieve GitHub API rate limit metrics."""
        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(f"{self.api_url}/rate_limit", headers=headers)
            resp.raise_for_status()
            return resp.json()

    def get_pull_request(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """Retrieve PR metadata (title, body, base ref, head ref, clone URL)."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def get_pull_request_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """Retrieve raw unified diff text for a pull request."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers(accept="application/vnd.github.v3.diff")
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text

    def get_pull_request_files(self, owner: str, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """Retrieve list of modified files in a pull request."""
        url = f"{self.api_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        headers = self._get_headers()
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def get_authenticated_clone_url(self, clone_url: str) -> str:
        """Insert GITHUB_TOKEN safely into HTTPS clone URL without printing."""
        if self.token and "github.com" in clone_url and "x-access-token" not in clone_url:
            return clone_url.replace("https://", f"https://x-access-token:{self.token}@")
        return clone_url

    def clone_and_checkout_pr(
        self,
        repo_url: str,
        pr_number: int,
        target_dir: str,
        base_ref: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clones repository using authentication, fetches PR branch, and generates unified diff.
        Returns dict with diff_text, base_ref, and repo object.
        """
        import git

        auth_url = self.get_authenticated_clone_url(repo_url)
        os.makedirs(target_dir, exist_ok=True)

        logger.info(f"Cloning repository to {target_dir}")
        repo = git.Repo.clone_from(auth_url, target_dir)

        logger.info(f"Fetching PR #{pr_number}")
        repo.git.fetch("origin", f"pull/{pr_number}/head:pr-{pr_number}")
        repo.git.checkout(f"pr-{pr_number}")

        # Determine base branch or default branch
        if not base_ref:
            try:
                base_ref = repo.active_branch.name
            except Exception:
                base_ref = "master" if "master" in [h.name for h in repo.heads] else "main"

        try:
            repo.git.fetch("origin", f"{base_ref}:{base_ref}")
        except Exception:
            pass

        # Try diffing against origin/base_ref, fallback to diff against origin/master, origin/main, or HEAD~1
        diff_text = ""
        for ref in [f"origin/{base_ref}", "origin/master", "origin/main", "origin/HEAD", "HEAD~1"]:
            try:
                diff_text = repo.git.diff(f"{ref}...HEAD")
                if diff_text:
                    break
            except Exception:
                continue

        if not diff_text:
            try:
                diff_text = repo.git.diff("HEAD~1")
            except Exception:
                diff_text = ""

        return {
            "diff_text": diff_text,
            "base_ref": base_ref,
            "target_dir": target_dir,
        }
