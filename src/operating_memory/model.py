"""Generic records exchanged between importer and storage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Entity:
    identity: str
    kind: str
    key: str
    title: str
    source_path: str
    body: str
    content_hash: str


@dataclass(frozen=True)
class Decision:
    identity: str
    entity_identity: str
    date: str
    body: str
    source_path: str
    content_hash: str


@dataclass(frozen=True)
class JournalEntry:
    identity: str
    date: str
    source_path: str
    body: str
    content_hash: str


@dataclass(frozen=True)
class ImportPlan:
    entities: tuple[Entity, ...]
    decisions: tuple[Decision, ...]
    journals: tuple[JournalEntry, ...]
    skipped: tuple[str, ...]


@dataclass(frozen=True)
class ImportReport:
    discovered: int
    created: int
    updated: int
    unchanged: int
    skipped: tuple[str, ...]
