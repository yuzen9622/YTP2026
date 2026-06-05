"""Document classifier for RAG documents.

Classifies documents based on metadata or filename patterns using rules
loaded from rag_config.yaml.
"""
from __future__ import annotations

import fnmatch
import logging
from dataclasses import dataclass
from typing import Optional

from app.domains.rag.value_objects import ClassificationRule, DocumentTag
from app.infrastructure.rag.config_loader import ClassificationConfig, TagRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    """Result of classifying a document.

    Attributes:
        primary_tag: The highest-priority matched tag (used for category field).
        tags: All matched tags for this document.
    """
    primary_tag: DocumentTag
    tags: frozenset[DocumentTag]


class DocumentClassifier:
    """Classifies documents based on configured rules."""

    def __init__(self, config: ClassificationConfig) -> None:
        self._config = config
        self._rules = config.get_rules()

    @property
    def tag_registry(self) -> TagRegistry:
        return self._config.tag_registry

    def classify(
        self,
        filename: str,
        metadata: Optional[dict] = None,
    ) -> ClassificationResult:
        """Classify a document by applying all matching rules.

        Rules are checked in priority order (highest first).
        Metadata-based rules are checked before filename-based rules.

        Args:
            filename: The document filename.
            metadata: Optional dict of metadata extracted from document.

        Returns:
            ClassificationResult with primary_tag and all matched tags.

        Raises:
            ValueError: If no rules match and no default is available.
        """
        matched: list[DocumentTag] = []
        metadata_rules: list[ClassificationRule] = []
        filename_rules: list[ClassificationRule] = []

        for rule in self._rules:
            if rule.source == "metadata":
                metadata_rules.append(rule)
            elif rule.source == "filename":
                filename_rules.append(rule)

        metadata_tags = self._check_metadata_rules(metadata, metadata_rules)
        matched.extend(metadata_tags)

        if not metadata_tags:
            filename_tags = self._check_filename_rules(filename, filename_rules)
            matched.extend(filename_tags)

        if not matched:
            raise ValueError(
                f"No classification rules matched for file: {filename}. "
                f"Add a rule in rag_config.yaml or rename the file with a known prefix."
            )

        unique_tags = list(dict.fromkeys(matched))
        primary_tag = unique_tags[0]

        return ClassificationResult(
            primary_tag=primary_tag,
            tags=frozenset(matched),
        )

    def _check_metadata_rules(
        self,
        metadata: Optional[dict],
        rules: list[ClassificationRule],
    ) -> list[DocumentTag]:
        """Check metadata-based classification rules."""
        if not metadata:
            return []

        matched: list[DocumentTag] = []
        for rule in rules:
            if rule.metadata_key and rule.metadata_key in metadata:
                value = metadata[rule.metadata_key]
                tag = self._match_tag_value(value, rule.tag)
                if tag:
                    matched.append(tag)
                    logger.debug(
                        "[classifier] metadata match: key={} value={} tag={}",
                        rule.metadata_key,
                        value,
                        tag.name,
                    )

        return matched

    def _match_tag_value(self, value: str, expected_tag: DocumentTag) -> Optional[DocumentTag]:
        """Check if a metadata value matches an expected tag."""
        if not value:
            return None

        value_lower = value.lower().strip()
        tag_names = [n.strip().lower() for n in value.split(",")]

        for name in tag_names:
            if name == expected_tag.name.lower() or name == expected_tag.display_name.lower():
                return expected_tag

        return None

    def _check_filename_rules(
        self,
        filename: str,
        rules: list[ClassificationRule],
    ) -> list[DocumentTag]:
        """Check filename-based classification rules."""
        matched: list[DocumentTag] = []

        for rule in rules:
            if rule.filename_pattern:
                if fnmatch.fnmatch(filename, rule.filename_pattern):
                    matched.append(rule.tag)
                    logger.debug(
                        "[classifier] filename match: pattern={} file={} tag={}",
                        rule.filename_pattern,
                        filename,
                        rule.tag.name,
                    )

        return matched


def build_classifier(config: Optional[ClassificationConfig] = None) -> DocumentClassifier:
    """Build a DocumentClassifier instance.

    Args:
        config: Optional pre-loaded config. If None, loads from rag_config.yaml.

    Returns:
        DocumentClassifier instance.
    """
    if config is None:
        from app.infrastructure.rag.config_loader import load_config
        config = load_config()
    return DocumentClassifier(config)
