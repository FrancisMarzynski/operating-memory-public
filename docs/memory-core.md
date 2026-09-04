# Local memory core

Operating Memory derives a SQLite database from Markdown notes. The notes remain authoritative; the database is a queryable local projection.

Copy `operating-memory.example.toml` to `operating-memory.toml`, then adapt every root, kind, and import rule to your own notes. Configuration is required to declare `version = 1`, `notes_root`, a non-empty `entity_kinds` list, and at least one `[[entities]]` rule; no root or kind is inferred.

Each entity rule uses a relative Markdown glob, a declared kind, and `key_from = "path"`. `title_from` may be `first_heading` or `filename` (which always uses the filename even if the note has an H1). Optional decisions use `path_template`, a safe relative path from each matched note's directory containing exactly one `{note_stem}` placeholder; for example, `{note_stem}.decisions.log` gives every note one unambiguous adjacent log. Decision lines must use a real calendar date in `YYYY-MM-DD — decision body` form; malformed lines are listed as skips. Journal rules are independent and derive their date from a filename using their configured `date_pattern`.

Run the CLI with both file locations explicitly supplied:

```sh
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite config validate
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite import --dry-run
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite import --apply
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite kinds
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite entity get project projects/orbit.md
PYTHONPATH=src python -m operating_memory.cli --config operating-memory.toml --database memory.sqlite decisions project projects/orbit.md
```

`import` has no implicit mode: it fails unless either `--dry-run` or `--apply` is present. Dry runs only read notes and never create or open the database; applies upsert deterministic records. Read-only commands open an existing SQLite database without creating a file or schema. An entity identity is derived from kind and source-relative path, while a decision identity derives from its entity, date, and body.

`MemoryRepository` is the v1 storage boundary. Adapter authors can preserve importer semantics by providing `upsert`, `list_kinds`, `get_entity`, and `decisions_for`; `MemoryStore` is the local SQLite implementation. Project tooling uses `PYTHONPATH=src python -m unittest discover -s tests` and `python scripts/check_boundary.py` before review.

The standard public boundary check rejects UI/runtime assets. During a private extraction and before release, maintainers must create the private policy in a maintainer-controlled location outside the checkout, keep it untracked, and supply its real absolute path at invocation time:

```sh
python scripts/check_boundary.py --require-policy --policy "$POLICY_FILE"
```

`POLICY_FILE` must name the existing private policy file; it is never a repository setting or public artifact. Release verification fails closed when it is omitted, unreadable, malformed, or empty. Each policy line is either `marker VALUE` or `path-prefix VALUE`.
