"""Command line interface for configuration-driven local memory."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Sequence

from .config import ConfigError, load_config
from .importer import apply_plan, build_plan
from .store import MemoryStore


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="om")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--database", required=True, type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    config = commands.add_parser("config")
    config.add_subparsers(dest="config_command", required=True).add_parser("validate")
    importing = commands.add_parser("import")
    mode = importing.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    commands.add_parser("kinds")
    entity = commands.add_parser("entity")
    get = entity.add_subparsers(dest="entity_command", required=True).add_parser("get")
    get.add_argument("kind")
    get.add_argument("key")
    decisions = commands.add_parser("decisions")
    decisions.add_argument("kind")
    decisions.add_argument("key")
    return parser


def _report(report: object) -> None:
    print(" ".join(f"{key}={value}" for key, value in report.__dict__.items() if key != "skipped"))
    for skipped in report.skipped:
        print(f"skipped: {skipped}")


def main(arguments: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = list(arguments) if arguments is not None else None
    try:
        args = parser.parse_args(arguments)
        config = load_config(args.config)
        if args.command == "config":
            print("configuration valid")
            return 0
        if args.command == "import":
            plan = build_plan(config)
            if args.dry_run:
                from .model import ImportReport
                _report(ImportReport(len(plan.entities) + len(plan.decisions) + len(plan.journals), 0, 0, 0, plan.skipped))
                return 0
            _report(apply_plan(MemoryStore(args.database), plan))
            return 0
        store = MemoryStore(args.database)
        if args.command == "kinds":
            print("\n".join(store.list_kinds()))
            return 0
        if args.command == "entity":
            entity = store.get_entity(args.kind, args.key)
            if entity is None:
                print("entity not found")
                return 1
            print(json.dumps({"kind": entity.kind, "key": entity.key, "title": entity.title, "source_path": entity.source_path, "body": entity.body}, sort_keys=True))
            return 0
        decisions = store.decisions_for(args.kind, args.key)
        print(json.dumps([{"date": decision.date, "body": decision.body, "source_path": decision.source_path} for decision in decisions], sort_keys=True))
        return 0
    except ConfigError as error:
        parser.error(str(error))
    except sqlite3.Error as error:
        parser.error(f"database is unavailable for read-only access: {error}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
