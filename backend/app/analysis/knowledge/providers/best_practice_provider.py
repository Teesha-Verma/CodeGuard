import os
import uuid
import logging

from app.analysis.knowledge.models import KnowledgeDocument
from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.providers.repository_provider import KnowledgeProvider

logger = logging.getLogger(__name__)

class BestPracticeProvider(KnowledgeProvider):
    """
    Provides coding best practice knowledge documents.
    
    Responsible for:
    - Python best practices
    - FastAPI patterns
    - Secure coding guidelines
    - Clean code principles
    """
    
    def __init__(self, knowledge_dir: str = "knowledge/best_practices"):
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
        return DocumentCategory.BEST_PRACTICE
    
    @property
    def provider_name(self) -> str:
        return "BestPracticeProvider"
        
    def _load_markdown_file(self, file_path: str) -> KnowledgeDocument | None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            title = os.path.basename(file_path)
            for line in content.splitlines():
                if line.startswith("# "):
                    title = line.strip("# ").strip()
                    break
            
            tags = ["best-practice"]
            lower_name = os.path.basename(file_path).lower()
            if "python" in lower_name:
                tags.append("python")
            if "fastapi" in lower_name:
                tags.append("fastapi")
                
            return KnowledgeDocument(
                document_id=str(uuid.uuid4()),
                title=title,
                content=content,
                category=self.get_category(),
                source=file_path,
                tags=tags
            )
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
