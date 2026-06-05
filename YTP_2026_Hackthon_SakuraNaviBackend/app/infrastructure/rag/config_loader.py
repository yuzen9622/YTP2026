"""YAML config loader for RAG classification rules and tags."""
from __future__ import annotations

import yaml
from pathlib import Path
from typing import Optional

from loguru import logger

from app.domains.rag.value_objects import ClassificationRule, DocumentTag


class TagRegistry:
    """Registry of all known document tags."""

    def __init__(self) -> None:
        self._tags: dict[str, DocumentTag] = {}

    def register(self, tag: DocumentTag) -> None:
        if tag.name in self._tags:
            raise ValueError(f"Duplicate tag name: {tag.name}")
        self._tags[tag.name] = tag

    def get(self, name: str) -> Optional[DocumentTag]:
        return self._tags.get(name)

    def get_or_raise(self, name: str) -> DocumentTag:
        tag = self._tags.get(name)
        if tag is None:
            raise ValueError(f"Unknown tag: {name}")
        return tag

    def all_tags(self) -> tuple[DocumentTag, ...]:
        return tuple(self._tags.values())

    @classmethod
    def from_yaml(cls, config: dict) -> "TagRegistry":
        registry = cls()
        for tag_def in config.get("tags", []):
            tag = DocumentTag(
                name=tag_def["name"],
                display_name=tag_def["display_name"],
                namespace=tag_def["namespace"],
            )
            registry.register(tag)
        return registry


class ClassificationConfig:
    """Classification rules loaded from YAML config."""

    def __init__(
        self,
        tag_registry: TagRegistry,
        rules: list[ClassificationRule],
    ) -> None:
        self._tag_registry = tag_registry
        self._rules = sorted(rules, key=lambda r: -r.priority)

    @property
    def tag_registry(self) -> TagRegistry:
        return self._tag_registry

    def get_rules(self) -> tuple[ClassificationRule, ...]:
        return tuple(self._rules)

    @classmethod
    def from_yaml(cls, config: dict) -> "ClassificationConfig":
        tag_registry = TagRegistry.from_yaml(config)
        rules: list[ClassificationRule] = []

        for rule_def in config.get("classification_rules", []):
            tag_name = rule_def["tag"]
            namespace = rule_def["namespace"]
            tag = tag_registry.get_or_raise(f"{tag_name}")

            rule = ClassificationRule(
                tag=tag,
                priority=rule_def.get("priority", 0),
                source=rule_def.get("source", "filename"),
                metadata_key=rule_def.get("metadata_key"),
                filename_pattern=rule_def.get("filename_pattern"),
            )
            rules.append(rule)

        return cls(tag_registry=tag_registry, rules=rules)


def load_config(config_path: Optional[Path] = None) -> ClassificationConfig:
    """Load classification config from YAML file.

    Args:
        config_path: Path to rag_config.yaml. If None, looks in project root.

    Returns:
        ClassificationConfig instance with tag registry and rules.
    """
    if config_path is None:
        project_root = Path(__file__).resolve().parents[3]
        config_path = project_root / "rag_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    loaded = ClassificationConfig.from_yaml(config)
    logger.info(
        "[rag] loaded {} tags and {} classification rules",
        len(loaded.tag_registry.all_tags()),
        len(loaded.get_rules()),
    )
    return loaded
