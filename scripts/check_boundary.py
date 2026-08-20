#!/usr/bin/env python3
"""Reject tracked content and paths that cross the extraction boundary."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


PUBLIC_PATH_PREFIXES = ("ui/", "app/", "pages/", "components/", "frontend/", "public/", "assets/", "static/", "bin/", "launchd/")
PUBLIC_PATH_SUFFIXES = (".tsx", ".jsx", ".vue", ".svelte", ".html", ".css", ".scss", ".sass", ".less", ".svg", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".woff", ".woff2", ".ttf", ".otf")


def _policy(path: Path | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if path is None:
        return (), ()
    markers: list[str] = []
    prefixes: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        kind, separator, value = line.partition(" ")
        if not separator or not value:
            raise ValueError(f"policy line {number} must be 'marker VALUE' or 'path-prefix VALUE'")
        if kind == "marker":
            markers.append(value)
        elif kind == "path-prefix":
            prefixes.append(value)
        else:
            raise ValueError(f"policy line {number} has unsupported rule {kind!r}")
    return tuple(markers), tuple(prefixes)


def main(root: Path | None = None, policy: Path | None = None, require_policy: bool = False) -> int:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    if require_policy and policy is None:
        raise ValueError("a private policy is required for release verification")
    policy_markers, policy_prefixes = _policy(policy)
    markers = tuple(marker.casefold() for marker in policy_markers)
    prefixes = tuple(prefix.casefold() for prefix in (*PUBLIC_PATH_PREFIXES, *policy_prefixes))
    suffixes = tuple(suffix.casefold() for suffix in PUBLIC_PATH_SUFFIXES)
    tracked = subprocess.run(["git", "ls-files"], cwd=root, check=True, text=True, capture_output=True).stdout.splitlines()
    violations: list[str] = []
    for relative in tracked:
        normalized_relative = relative.casefold()
        if normalized_relative.startswith(prefixes) or normalized_relative.endswith(suffixes):
            violations.append(f"{relative}: prohibited boundary path")
            continue
        if any(marker in normalized_relative for marker in markers):
            violations.append(f"{relative}: prohibited boundary marker")
            continue
        path = root / relative
        if not path.is_file():
            continue
        content = path.read_bytes().decode("utf-8", errors="ignore").casefold()
        if any(marker in content for marker in markers):
            violations.append(f"{relative}: prohibited boundary marker")
    if violations:
        print("\n".join(violations), file=sys.stderr)
        return 1
    return 0


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--require-policy", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = _arguments()
    try:
        raise SystemExit(main(args.root, args.policy, args.require_policy))
    except (OSError, ValueError) as error:
        print(f"boundary policy error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
