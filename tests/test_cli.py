from __future__ import annotations

import io
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from operating_memory.cli import main


class CliTests(unittest.TestCase):
    def test_import_requires_an_explicit_mode(self) -> None:
        with self.assertRaises(SystemExit) as exited:
            main(["--config", "missing.toml", "--database", "memory.sqlite", "import"])
        self.assertEqual(exited.exception.code, 2)

    def test_apply_then_reads_entity_and_decisions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "notes/items").mkdir(parents=True)
            (root / "notes/items/one.md").write_text("# One\n\nBody", encoding="utf-8")
            (root / "notes/items/one.choices.log").write_text(
                "2026-02-01 — Keep it local.\n", encoding="utf-8"
            )
            (root / "operating-memory.toml").write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "items/*.md"
key_from = "path"
[entities.decisions]
path_template = "{note_stem}.choices.log"
""",
                encoding="utf-8",
            )
            database = root / "memory.sqlite"
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(
                    main(
                        [
                            "--config",
                            str(root / "operating-memory.toml"),
                            "--database",
                            str(database),
                            "import",
                            "--apply",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "--config",
                            str(root / "operating-memory.toml"),
                            "--database",
                            str(database),
                            "entity",
                            "get",
                            "item",
                            "items/one.md",
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    main(
                        [
                            "--config",
                            str(root / "operating-memory.toml"),
                            "--database",
                            str(database),
                            "decisions",
                            "item",
                            "items/one.md",
                        ]
                    ),
                    0,
                )
            self.assertIn("created=2", output.getvalue())
            self.assertIn("One", output.getvalue())
            self.assertIn("Keep it local.", output.getvalue())

    def test_apply_closes_connection_when_schema_setup_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "notes").mkdir()
            (root / "notes" / "one.md").write_text("# One\n", encoding="utf-8")
            (root / "operating-memory.toml").write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
""",
                encoding="utf-8",
            )
            database = root / "memory.sqlite"
            database.write_text("not a database", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-W",
                    "error::ResourceWarning",
                    "-m",
                    "operating_memory.cli",
                    "--config",
                    str(root / "operating-memory.toml"),
                    "--database",
                    str(database),
                    "import",
                    "--apply",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("ResourceWarning", result.stderr)

    def test_read_only_commands_do_not_create_a_database_or_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "notes").mkdir()
            config = root / "operating-memory.toml"
            config.write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
""",
                encoding="utf-8",
            )
            database = root / "missing.sqlite"
            self.assertEqual(
                main(["--config", str(config), "--database", str(database), "import", "--dry-run"]),
                0,
            )
            self.assertFalse(database.exists())
            with self.assertRaises(SystemExit) as exited:
                main(["--config", str(config), "--database", str(database), "kinds"])
            self.assertEqual(exited.exception.code, 2)
            self.assertFalse(database.exists())
            database.touch()
            with self.assertRaises(SystemExit) as exited:
                main(["--config", str(config), "--database", str(database), "kinds"])
            self.assertEqual(exited.exception.code, 2)
            connection = sqlite3.connect(database)
            try:
                tables = connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            finally:
                connection.close()
            self.assertEqual(tables, [])
            self.assertEqual(
                main(["--config", str(config), "--database", str(database), "config", "validate"]),
                0,
            )
            self.assertTrue(database.exists())
