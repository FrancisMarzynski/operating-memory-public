"""Explicit, versioned configuration for an import."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path


class ConfigError(ValueError):
    """A configuration field is missing or invalid."""


@dataclass(frozen=True)
class DecisionRule:
    path_template: str


@dataclass(frozen=True)
class EntityRule:
    kind: str
    glob: str
    key_from: str
    title_from: str
    decisions: DecisionRule | None = None


@dataclass(frozen=True)
class JournalRule:
    glob: str
    date_pattern: str


@dataclass(frozen=True)
class MemoryConfig:
    version: int
    notes_root: Path
    entity_kinds: tuple[str, ...]
    entities: tuple[EntityRule, ...]
    journals: tuple[JournalRule, ...]


def _required_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{field} must be a non-empty string")
    return value


def load_config(path: Path) -> MemoryConfig:
    """Load v1 configuration without supplying roots or kinds implicitly."""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ConfigError(f"config file not found: {path}") from error
    except tomllib.TOMLDecodeError as error:
        raise ConfigError(f"configuration TOML is invalid: {error}") from error

    version = raw.get("version")
    if type(version) is not int or version != 1:
        raise ConfigError("version must be 1")
    notes_root_value = _required_string(raw.get("notes_root"), "notes_root")
    notes_root = (path.parent / notes_root_value).resolve()
    kinds = raw.get("entity_kinds")
    if (
        not isinstance(kinds, list)
        or not kinds
        or any(not isinstance(kind, str) or not kind for kind in kinds)
    ):
        raise ConfigError("entity_kinds must be a non-empty list of strings")

    raw_entities = raw.get("entities")
    if not isinstance(raw_entities, list) or not raw_entities:
        raise ConfigError("entities must contain one or more entity rules")
    entities: list[EntityRule] = []
    for index, item in enumerate(raw_entities):
        field = f"entities[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{field} must be a table")
        kind = _required_string(item.get("kind"), f"{field}.kind")
        if kind not in kinds:
            raise ConfigError(f"{field}.kind must appear in entity_kinds")
        key_from = _required_string(item.get("key_from"), f"{field}.key_from")
        if key_from != "path":
            raise ConfigError(f"{field}.key_from must be path")
        title_from = item.get("title_from", "filename")
        if title_from not in {"filename", "first_heading"}:
            raise ConfigError(f"{field}.title_from must be filename or first_heading")
        decision_rule = None
        decision = item.get("decisions")
        if decision is not None:
            if not isinstance(decision, dict):
                raise ConfigError(f"{field}.decisions must be a table")
            template_field = f"{field}.decisions.path_template"
            template = _safe_relative(
                _required_string(decision.get("path_template"), template_field), template_field
            )
            remainder = template.replace("{note_stem}", "")
            if template.count("{note_stem}") != 1 or "{" in remainder or "}" in remainder:
                raise ConfigError(
                    f"{template_field} must contain exactly one {{note_stem}} placeholder"
                )
            decision_rule = DecisionRule(template)
        entities.append(
            EntityRule(
                kind,
                _safe_relative(
                    _required_string(item.get("glob"), f"{field}.glob"), f"{field}.glob"
                ),
                key_from,
                title_from,
                decision_rule,
            )
        )

    journals: list[JournalRule] = []
    for index, item in enumerate(raw.get("journals", [])):
        field = f"journals[{index}]"
        if not isinstance(item, dict):
            raise ConfigError(f"{field} must be a table")
        journals.append(
            JournalRule(
                _safe_relative(
                    _required_string(item.get("glob"), f"{field}.glob"), f"{field}.glob"
                ),
                _required_string(item.get("date_pattern"), f"{field}.date_pattern"),
            )
        )
    return MemoryConfig(1, notes_root, tuple(kinds), tuple(entities), tuple(journals))


def _safe_relative(value: str, field: str) -> str:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ConfigError(f"{field} must be relative to notes_root and cannot escape it")
    return value
