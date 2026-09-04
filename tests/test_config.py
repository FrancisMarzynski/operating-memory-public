from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from operating_memory.config import ConfigError, load_config


class ConfigTests(unittest.TestCase):
    def test_loads_explicit_versioned_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "notes" / "projects").mkdir(parents=True)
            config_path = root / "operating-memory.toml"
            config_path.write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["project", "reference"]

[[entities]]
kind = "project"
glob = "projects/**/*.md"
key_from = "path"
title_from = "first_heading"
""",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config.version, 1)
            self.assertEqual(config.notes_root, (root / "notes").resolve())
            self.assertEqual(config.entities[0].kind, "project")

    def test_rejects_missing_entity_kinds(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "operating-memory.toml"
            config_path.write_text('version = 1\nnotes_root = "notes"\n', encoding="utf-8")

            with self.assertRaisesRegex(ConfigError, "entity_kinds"):
                load_config(config_path)

    def test_requires_a_true_integer_version_and_safe_per_note_log_template(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "operating-memory.toml"
            config_path.write_text(
                """version = true
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "version"):
                load_config(config_path)
            config_path.write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
[entities.decisions]
path_template = "decisions.log"
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "path_template"):
                load_config(config_path)

    def test_rejects_rule_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "operating-memory.toml"
            config_path.write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "../outside/*.md"
key_from = "path"
""",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ConfigError, "cannot escape"):
                load_config(config_path)

    def test_decision_line_template_defaults_to_the_existing_format(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "operating-memory.toml"
            config_path.write_text(
                """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
[entities.decisions]
path_template = "{note_stem}.decisions.log"
""",
                encoding="utf-8",
            )

            config = load_config(config_path)

            self.assertEqual(config.entities[0].decisions.line_template, "{date} — {body}")

    def test_rejects_malformed_decision_line_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "operating-memory.toml"
            base = """version = 1
notes_root = "notes"
entity_kinds = ["item"]
[[entities]]
kind = "item"
glob = "*.md"
key_from = "path"
[entities.decisions]
path_template = "{note_stem}.decisions.log"
line_template = %r
"""
            for template, reason in (
                ("{date} — decision", "{body}"),
                ("{date} — {body} {body}", "exactly once"),
                ("{date}: {summary}", "unrecognised placeholder"),
            ):
                with self.subTest(template=template):
                    config_path.write_text(base % template, encoding="utf-8")

                    with self.assertRaisesRegex(
                        ConfigError, r"entities\[0\]\.decisions\.line_template.*" + reason
                    ):
                        load_config(config_path)
