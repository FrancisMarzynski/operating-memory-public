from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class BoundaryTests(unittest.TestCase):
    def test_tracked_content_passes_public_guard(self) -> None:
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "scripts/check_boundary.py"], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_private_policy_rejects_configured_content_and_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "private-root").mkdir()
            (root / "private-root" / "note.md").write_text("ordinary text", encoding="utf-8")
            (root / "note.md").write_text("private-identifier", encoding="utf-8")
            policy = root / "policy.txt"
            policy.write_text("marker private-identifier\npath-prefix private-root/\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)

            guard = Path(__file__).resolve().parents[1] / "scripts/check_boundary.py"
            result = subprocess.run([sys.executable, str(guard), str(root), "--policy", str(policy)], text=True, capture_output=True)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("prohibited boundary path", result.stderr)
            self.assertIn("prohibited boundary marker", result.stderr)

    def test_private_policy_matches_binary_content_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "asset.bin").write_bytes(b"\x00pRiVaTe-IdEnTiFiEr\xff")
            policy = root / "policy.txt"
            policy.write_text("marker private-identifier\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)

            guard = Path(__file__).resolve().parents[1] / "scripts/check_boundary.py"
            result = subprocess.run([sys.executable, str(guard), str(root), "--policy", str(policy)], text=True, capture_output=True)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("asset.bin: prohibited boundary marker", result.stderr)

    def test_public_guard_rejects_ui_assets_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "UI").mkdir()
            (root / "UI" / "screen.tsx").write_text("generic", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)

            guard = Path(__file__).resolve().parents[1] / "scripts/check_boundary.py"
            result = subprocess.run([sys.executable, str(guard), str(root)], text=True, capture_output=True)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("UI/screen.tsx: prohibited boundary path", result.stderr)

    def test_rejects_malformed_private_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            (root / "note.md").write_text("generic", encoding="utf-8")
            policy = root / "policy.txt"
            policy.write_text("unknown value\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)

            guard = Path(__file__).resolve().parents[1] / "scripts/check_boundary.py"
            result = subprocess.run([sys.executable, str(guard), str(root), "--policy", str(policy)], text=True, capture_output=True)

            self.assertEqual(result.returncode, 2)
            self.assertIn("boundary policy error", result.stderr)
