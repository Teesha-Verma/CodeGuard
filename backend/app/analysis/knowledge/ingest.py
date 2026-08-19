"""
Knowledge Ingestion & Vector Refresh CLI.

Usage:
    python -m app.analysis.knowledge.ingest [--force]
"""
import sys
import logging
from app.analysis.RAG.knowledge_retrieval_service import KnowledgeRetrievalService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    force = "--force" in sys.argv or "-f" in sys.argv
    logger.info(f"Starting knowledge base ingestion (force_reindex={force})...")
    service = KnowledgeRetrievalService.get_instance()
    count = service.index_knowledge_base(force_reindex=force)
    logger.info(f"Ingestion finished successfully: {count} vectors stored.")


if __name__ == "__main__":
    main()
