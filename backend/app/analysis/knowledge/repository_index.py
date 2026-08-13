import logging
from typing import Any

from app.analysis.knowledge.models import RepositoryContext

logger = logging.getLogger(__name__)

class RepositoryIndex:
    """
    Stores and retrieves repository intelligence metadata.
    
    This module provides structured lookup for repository-specific context
    such as language, framework, dependencies, architecture, and analysis summaries.
    
    This module does NOT perform vector search.
    """
    
    def __init__(self) -> None:
        self._repositories: dict[str, RepositoryContext] = {}
    
    def index_repository(self, context: RepositoryContext) -> None:
        """Store or update repository context."""
        try:
            # Assuming RepositoryContext has a repository_url property
            repo_url = getattr(context, 'repository_url', str(id(context)))
            self._repositories[repo_url] = context
            logger.info(f"Indexed repository context for {repo_url}")
        except Exception as e:
            logger.error(f"Failed to index repository: {e}")
            raise
    
    def get_context(self, repository_url: str) -> RepositoryContext | None:
        """Retrieve repository context by URL."""
        return self._repositories.get(repository_url)
    
    def update_cfg_summary(self, repository_url: str, cfg_summary: dict[str, Any]) -> None:
        """Update CFG summary for a repository."""
        context = self.get_context(repository_url)
        if context:
            setattr(context, 'cfg_summary', cfg_summary)
            logger.debug(f"Updated CFG summary for {repository_url}")
        else:
            logger.warning(f"Repository {repository_url} not found for CFG update")
    
    def update_call_graph_summary(self, repository_url: str, call_graph_summary: dict[str, Any]) -> None:
        context = self.get_context(repository_url)
        if context:
            setattr(context, 'call_graph_summary', call_graph_summary)
            logger.debug(f"Updated call graph summary for {repository_url}")
        else:
            logger.warning(f"Repository {repository_url} not found for call graph update")
    
    def update_data_flow_summary(self, repository_url: str, data_flow_summary: dict[str, Any]) -> None:
        context = self.get_context(repository_url)
        if context:
            setattr(context, 'data_flow_summary', data_flow_summary)
            logger.debug(f"Updated data flow summary for {repository_url}")
        else:
            logger.warning(f"Repository {repository_url} not found for data flow update")
    
    def list_repositories(self) -> list[str]:
        """List all indexed repository URLs."""
        return list(self._repositories.keys())
    
    def remove_repository(self, repository_url: str) -> bool:
        if repository_url in self._repositories:
            del self._repositories[repository_url]
            logger.info(f"Removed repository {repository_url}")
            return True
        return False
    
    def get_dependencies(self, repository_url: str) -> list[str]:
        context = self.get_context(repository_url)
        if context and hasattr(context, 'dependencies'):
            return context.dependencies or []
        return []
    
    def get_framework(self, repository_url: str) -> str:
        context = self.get_context(repository_url)
        if context and hasattr(context, 'framework'):
            return context.framework or ""
        return ""
