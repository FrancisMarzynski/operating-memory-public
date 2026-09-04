from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from operating_memory.config import load_config
from operating_memory.importer import apply_plan, build_plan
from operating_memory.store import MemoryStore

CONFIG = """version = 1
notes_root = "notes"
entity_kinds = ["project", "reference"]

[[entities]]
kind = "project"
glob = "projects/**/*.md"
key_from = "path"
title_from = "first_heading"

[entities.decisions]
path_template = "{note_stem}.decisions.log"

[[entities]]
kind = "reference"
glob = "references/*.md"
key_from = "path"

[[journals]]
glob = "journal/*.md"
date_pattern = "%Y-%m-%d"
"""


class RecordingRepository:
    def __init__(self) -> None:
        self.records: list[object] = []

    def upsert(self, record: object) -> str:
        self.records.append(record)
        return "created"

    def list_kinds(self) -> list[str]:
        return []

    def get_entity(self, kind: str, key: str) -> object | None:
        return None

    def decisions_for(self, kind: str, key: str) -> list[object]:
        return []


class ImporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        (self.root / "notes/projects/nested").mkdir(parents=True)
        (self.root / "notes/references").mkdir()
        (self.root / "notes/journal").mkdir()
        (self.root / "operating-memory.toml").write_text(CONFIG, encoding="utf-8")
        (self.root / "notes/projects/nested/atlas.md").write_text(
            "# Atlas\n\nA generic project.\n", encoding="utf-8"
        )
        (self.root / "notes/projects/nested/atlas.decisions.log").write_text(
            "2026-01-03 — Begin with a local store.\nbad line\n", encoding="utf-8"
        )
        (self.root / "notes/references/guide.md").write_text("Reference body", encoding="utf-8")
        (self.root / "notes/journal/2026-01-04.md").write_text("Journal body", encoding="utf-8")
        self.config = load_config(self.root / "operating-memory.toml")

    def tearDown(self) -> None:
        self.directory.cleanup()

    def test_dry_plan_discovers_records_without_creating_database(self) -> None:
        plan = build_plan(self.config)

        self.assertEqual(len(plan.entities), 2)
        self.assertEqual(len(plan.decisions), 1)
        self.assertEqual(len(plan.journals), 1)
        self.assertEqual(
            plan.skipped, ("projects/nested/atlas.decisions.log: invalid decision line 2",)
        )
        self.assertFalse((self.root / "memory.sqlite").exists())

    def test_apply_is_idempotent_and_updates_changed_note(self) -> None:
        database = self.root / "memory.sqlite"
        first = apply_plan(MemoryStore(database), build_plan(self.config))
        second = apply_plan(MemoryStore(database), build_plan(self.config))
        (self.root / "notes/references/guide.md").write_text("Changed reference", encoding="utf-8")
        third = apply_plan(MemoryStore(database), build_plan(self.config))

        self.assertEqual((first.created, first.updated, first.unchanged), (4, 0, 0))
        self.assertEqual((second.created, second.updated, second.unchanged), (0, 0, 4))
        self.assertEqual((third.created, third.updated, third.unchanged), (0, 1, 3))
        entity = MemoryStore(database).get_entity("reference", "references/guide.md")
        self.assertEqual(entity.body, "Changed reference")

    def test_filename_titles_and_derived_fields_update_records(self) -> None:
        database = self.root / "memory.sqlite"
        apply_plan(MemoryStore(database), build_plan(self.config))
        config_text = CONFIG.replace('title_from = "first_heading"', 'title_from = "filename"')
        config_text = config_text.replace("{note_stem}.decisions.log", "{note_stem}.ledger.log")
        config_text = config_text.replace('date_pattern = "%Y-%m-%d"', 'date_pattern = "%Y-%d-%m"')
        (self.root / "operating-memory.toml").write_text(config_text, encoding="utf-8")
        (self.root / "notes/projects/nested/atlas.ledger.log").write_text(
            "2026-01-03 — Begin with a local store.\n", encoding="utf-8"
        )
        report = apply_plan(
            MemoryStore(database), build_plan(load_config(self.root / "operating-memory.toml"))
        )

        self.assertEqual(report.updated, 3)
        entity = MemoryStore(database).get_entity("project", "projects/nested/atlas.md")
        self.assertEqual(entity.title, "atlas")
        decision = MemoryStore(database).decisions_for("project", "projects/nested/atlas.md")[0]
        self.assertEqual(decision.source_path, "projects/nested/atlas.ledger.log")
        connection = sqlite3.connect(database)
        try:
            journal_date = connection.execute("SELECT date FROM journals").fetchone()[0]
        finally:
            connection.close()
        self.assertEqual(journal_date, "2026-04-01")

    def test_first_heading_supports_markdown_headings_and_skips_code_fences(self) -> None:
        (self.root / "notes/projects/nested/atlas.md").write_text(
            "```markdown\n# Not the title\n```\n\nAtlas heading\n===\n", encoding="utf-8"
        )

        plan = build_plan(self.config)

        self.assertEqual(plan.entities[0].title, "Atlas heading")

    def test_importer_accepts_a_non_sqlite_repository(self) -> None:
        repository = RecordingRepository()

        report = apply_plan(repository, build_plan(self.config))

        self.assertEqual(report.created, 4)
        self.assertEqual(len(repository.records), 4)

    def test_per_note_logs_and_invalid_calendar_dates(self) -> None:
        (self.root / "notes/projects/nested/boreal.md").write_text("# Boreal", encoding="utf-8")
        (self.root / "notes/projects/nested/boreal.decisions.log").write_text(
            "2026-02-30 — Impossible date.\n2026-02-02 — Separate log.\n", encoding="utf-8"
        )
        plan = build_plan(self.config)

        self.assertEqual(len(plan.decisions), 2)
        self.assertIn(
            "projects/nested/boreal.decisions.log: invalid decision date on line 1", plan.skipped
        )
        self.assertEqual(
            {decision.source_path for decision in plan.decisions},
            {"projects/nested/atlas.decisions.log", "projects/nested/boreal.decisions.log"},
        )

    def test_imports_a_configured_decision_line_separator_and_reports_non_matches(self) -> None:
        config_text = CONFIG.replace(
            'path_template = "{note_stem}.decisions.log"',
            'path_template = "{note_stem}.decisions.log"\nline_template = "{date}: {body}"',
        )
        (self.root / "operating-memory.toml").write_text(config_text, encoding="utf-8")
        (self.root / "notes/projects/nested/atlas.decisions.log").write_text(
            "2026-01-03: Begin with a local store.\n2026-01-04 — Wrong separator.\n",
            encoding="utf-8",
        )

        plan = build_plan(load_config(self.root / "operating-memory.toml"))

        self.assertEqual(len(plan.decisions), 1)
        self.assertEqual(plan.decisions[0].body, "Begin with a local store.")
        self.assertEqual(
            plan.skipped,
            ("projects/nested/atlas.decisions.log: invalid decision line 2",),
        )

    def test_unreadable_optional_decision_logs_are_skipped(self) -> None:
        directory_log = self.root / "notes/projects/nested/atlas.decisions.log"
        directory_log.unlink()
        directory_log.mkdir()
        binary_log = self.root / "notes/projects/nested/boreal.decisions.log"
        (self.root / "notes/projects/nested/boreal.md").write_text("# Boreal", encoding="utf-8")
        binary_log.write_bytes(b"\xff\xfe")

        plan = build_plan(self.config)

        self.assertEqual(len(plan.decisions), 0)
        self.assertEqual(
            plan.skipped,
            (
                "projects/nested/atlas.decisions.log: unable to read decision log",
                "projects/nested/boreal.decisions.log: unable to read decision log",
            ),
        )

    def test_unreadable_optional_journals_are_skipped(self) -> None:
        (self.root / "notes/journal/2026-01-04.md").write_bytes(b"\xff\xfe")

        plan = build_plan(self.config)

        self.assertEqual(len(plan.entities), 2)
        self.assertEqual(len(plan.journals), 0)
        self.assertIn("journal/2026-01-04.md: unable to read journal", plan.skipped)

    def test_unreadable_entity_notes_are_skipped(self) -> None:
        (self.root / "notes/projects/nested/atlas.md").write_bytes(b"\xff\xfe")

        plan = build_plan(self.config)

        self.assertEqual(len(plan.entities), 1)
        self.assertIn("projects/nested/atlas.md: unable to read entity note", plan.skipped)

    def test_rejects_symlinked_note_outside_notes_root(self) -> None:
        outside = self.root / "outside.md"
        outside.write_text("# Outside", encoding="utf-8")
        link = self.root / "notes/projects/nested/escape.md"
        try:
            link.symlink_to(outside)
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")

        with self.assertRaisesRegex(ValueError, "escapes notes_root"):
            build_plan(self.config)
