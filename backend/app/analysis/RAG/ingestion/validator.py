"""Knowledge document validation.

Validates parsed documents for required metadata fields,
section presence, and content quality.
"""
from __future__ import annotations

from app.analysis.RAG.models.documents import KnowledgeDocument, ValidationResult
from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("validator")

# Required metadata fields
_REQUIRED_FIELDS = ["document_id", "title", "category"]

# Recommended sections (at least some should be present)
_RECOMMENDED_SECTIONS = [
    "Overview", "Why it matters", "Why This Matters",
    "Detection Rules", "Detection Guidance",
    "Bad Code Patterns", "Good Code Patterns",
    "Common Mistakes", "Secure Alternatives",
    "References",
]


def validate_document(doc: KnowledgeDocument) -> ValidationResult:
    """Validate a parsed knowledge document.
    
    Checks:
    - Required metadata fields are present and non-empty.
    - At least some recommended sections are present.
    - Body content is non-trivial.
    """
    result = ValidationResult(
        document_path=doc.source_path,
        metadata_present=bool(doc.metadata.document_id and doc.metadata.title),
        sections_found=list(doc.sections.keys()),
    )

    # Check required metadata
    for field_name in _REQUIRED_FIELDS:
        value = getattr(doc.metadata, field_name, None)
        if not value or (isinstance(value, str) and not value.strip()):
            result.add_error(field_name, f"Required field '{field_name}' is missing or empty")

    # Check body content
    if len(doc.body.strip()) < 50:
        result.add_warning("body", "Document body is very short (< 50 characters)")

    # Check sections
    found_recommended = [
        s for s in doc.sections
        if any(r.lower() in s.lower() for r in _RECOMMENDED_SECTIONS)
    ]
    if not found_recommended:
        result.add_warning("sections", "No recommended sections found")

    # Check tags
    if not doc.metadata.tags:
        result.add_warning("tags", "No tags defined")

    return result


def validate_batch(documents: list[KnowledgeDocument]) -> list[ValidationResult]:
    """Validate a batch of documents, returning all results."""
    results = []
    for doc in documents:
        vr = validate_document(doc)
        if not vr.is_valid:
            logger.warning(
                "Validation failed for '%s': %d errors",
                doc.source_path, len([i for i in vr.issues if i.severity == "error"]),
            )
        results.append(vr)
    return results
