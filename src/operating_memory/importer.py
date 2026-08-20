"""Deterministic planning and explicit application of note imports."""

from __future__ import annotations

from datetime import date as calendar_date
from datetime import datetime
from dataclasses import replace
import hashlib
from pathlib import Path
import re

from .config import MemoryConfig
from .model import Decision, Entity, ImportPlan, ImportReport, JournalEntry
from .store import MemoryRepository


DECISION_LINE = re.compile(r"(\d{4}-\d{2}-\d{2}) — (.+)")


def _hash(*values: str) -> str:
    return hashlib.sha256("\0".join(values).encode("utf-8")).hexdigest()


def _relative(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(f"source path escapes notes_root: {path}") from error


HEADING = re.compile(r"^ {0,3}#{1,6}[ \t]+(.+?)(?:[ \t]+#+)?[ \t]*$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)[ \t]*$")
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def _title(body: str, fallback: str, source: str) -> str:
    if source == "filename":
        return fallback
    fence: str | None = None
    lines = body.splitlines()
    for index, line in enumerate(lines):
        fence_match = FENCE.match(line)
        if fence_match:
            delimiter = fence_match.group(1)
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence):
                fence = None
            continue
        if fence is not None:
            continue
        match = HEADING.match(line)
        if match and match.group(1).strip():
            return match.group(1).strip()
        if line.strip() and index + 1 < len(lines) and SETEXT_UNDERLINE.match(lines[index + 1]):
            return line.strip()
    return fallback


def _entity_hash(entity: Entity) -> str:
    return _hash(entity.identity, entity.kind, entity.key, entity.title, entity.source_path, entity.body)


def _decision_hash(decision: Decision) -> str:
    return _hash(decision.identity, decision.entity_identity, decision.date, decision.body, decision.source_path)


def _journal_hash(journal: JournalEntry) -> str:
    return _hash(journal.identity, journal.date, journal.source_path, journal.body)


def build_plan(config: MemoryConfig) -> ImportPlan:
    """Read configured paths and produce a plan without opening a database."""
    entities: list[Entity] = []
    decisions: list[Decision] = []
    journals: list[JournalEntry] = []
    skipped: list[str] = []
    root = config.notes_root
    for rule in config.entities:
        for path in sorted(root.glob(rule.glob)):
            if not path.is_file():
                continue
            relative = _relative(root, path)
            try:
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                skipped.append(f"{relative}: unable to read entity note")
                continue
            identity = _hash(rule.kind, relative)
            entity = Entity(identity, rule.kind, relative, _title(body, path.stem, rule.title_from), relative, body, "")
            entities.append(replace(entity, content_hash=_entity_hash(entity)))
            if rule.decisions:
                log_path = path.parent / rule.decisions.path_template.replace("{note_stem}", path.stem)
                if log_path.exists():
                    log_relative = _relative(root, log_path)
                    try:
                        log_lines = log_path.read_text(encoding="utf-8").splitlines()
                    except (OSError, UnicodeDecodeError):
                        skipped.append(f"{log_relative}: unable to read decision log")
                        continue
                    for number, line in enumerate(log_lines, 1):
                        match = DECISION_LINE.fullmatch(line)
                        if not match:
                            skipped.append(f"{log_relative}: invalid decision line {number}")
                            continue
                        date, decision_body = match.groups()
                        try:
                            calendar_date.fromisoformat(date)
                        except ValueError:
                            skipped.append(f"{log_relative}: invalid decision date on line {number}")
                            continue
                        decision = Decision(_hash(identity, date, decision_body), identity, date, decision_body, log_relative, "")
                        decisions.append(replace(decision, content_hash=_decision_hash(decision)))
    for rule in config.journals:
        for path in sorted(root.glob(rule.glob)):
            if not path.is_file():
                continue
            relative = _relative(root, path)
            try:
                date = datetime.strptime(path.stem, rule.date_pattern).date().isoformat()
            except ValueError:
                skipped.append(f"{relative}: filename does not match journal date_pattern")
                continue
            try:
                body = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                skipped.append(f"{relative}: unable to read journal")
                continue
            journal = JournalEntry(_hash("journal", relative), date, relative, body, "")
            journals.append(replace(journal, content_hash=_journal_hash(journal)))
    return ImportPlan(tuple(entities), tuple(decisions), tuple(journals), tuple(skipped))


def apply_plan(store: MemoryRepository, plan: ImportPlan) -> ImportReport:
    counts = {"created": 0, "updated": 0, "unchanged": 0}
    records = (*plan.entities, *plan.decisions, *plan.journals)
    for record in records:
        counts[store.upsert(record)] += 1
    return ImportReport(len(records), counts["created"], counts["updated"], counts["unchanged"], plan.skipped)
