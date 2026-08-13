import os
import uuid
import logging
from abc import ABC, abstractmethod

from app.analysis.knowledge.models import KnowledgeDocument
from app.analysis.knowledge.constants import DocumentCategory

logger = logging.getLogger(__name__)

class KnowledgeProvider(ABC):
    """Abstract base interface for all knowledge providers."""
    
    @abstractmethod
    def load_documents(self) -> list[KnowledgeDocument]:
        """Load and return knowledge documents."""
        ...
    
    @abstractmethod
    def get_category(self) -> DocumentCategory:
        """Return the document category this provider serves."""
        ...
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Human-readable provider name."""
        ...

class RepositoryProvider(KnowledgeProvider):
    """
    Provides repository-specific knowledge documents.
    
    Responsible for:
    - Repository-specific rules and conventions
    - Ignore rules (files/patterns to skip)
    - Architecture conventions
    - Project-specific coding standards
    """
    
    def __init__(self, knowledge_dir: str = "knowledge/repository"):
        self._knowledge_dir = knowledge_dir
    
    def load_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        if not os.path.isdir(self._knowledge_dir):
            logger.warning(f"Directory not found: {self._knowledge_dir}")
            return documents
            
        for root, _, files in os.walk(self._knowledge_dir):
            for file in files:
                if file.endswith(".md"):
                    file_path = os.path.join(root, file)
                    doc = self._load_markdown_file(file_path)
                    if doc:
                        documents.append(doc)
        return documents
    
    def get_category(self) -> DocumentCategory:
        return DocumentCategory.REPOSITORY
    
    @property
    def provider_name(self) -> str:
        return "RepositoryProvider"
    
    def _load_markdown_file(self, file_path: str) -> KnowledgeDocument | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            title = os.path.basename(file_path)
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line.strip("# ").strip()
                    break
            
            return KnowledgeDocument(
                document_id=str(uuid.uuid4()),
                title=title,
                content=content,
                category=self.get_category(),
                source=file_path,
                tags=["repository"]
            )
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
