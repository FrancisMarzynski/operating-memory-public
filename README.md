# Operating Memory

[![CI](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml)

Operating Memory is a small, markdown-first memory core. It keeps durable notes
authoritative and derives a local SQLite projection from them for queries.

## Memory model

The source records are ordinary Markdown files:

- **Entities** describe durable things, such as a project or reference.
- **Decisions** are append-only dated lines associated with an entity. The
  line format is declared in configuration, so your own decision-log
  convention works without changing code.
- **Journal entries** are dated Markdown files for temporal records.

The database is derived data, never a replacement for those notes. Record
identities are deterministic: they use kind and source-relative location, with
decision date and body included where needed. Imports are therefore idempotent:
importing the same notes again changes nothing.

This repository is a deliberately small, generalised public extraction of a
larger private operating-memory system. The private system is demonstrated live
rather than shared; its architecture is described in
[the private-system architecture guide](docs/private-system-architecture.md)
without exposing its data, configuration, or integrations.

## Quick start

The repository includes an invented note corpus. From a fresh clone, run these
commands verbatim:

```sh
uv sync --group dev
om_example_dir="$(mktemp -d)"
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" config validate
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" import --dry-run
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" import --apply
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" kinds
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" entity get project projects/orbit.md
uv run om --config operating-memory.example.toml --database "$om_example_dir/memory.sqlite" decisions project projects/orbit.md
```

Adapt `operating-memory.example.toml` and the example notes to point at your own
Markdown files. If your decision logs do not use the default
`{date} — {body}` form, declare your own, for example:

```toml
[entities.decisions]
path_template = "{note_stem}.decisions.log"
line_template = "{date} | {body}"
```

Malformed templates are rejected when the configuration loads, with an error
naming the field. [The local memory-core guide](docs/memory-core.md) documents the
configuration format and command semantics.

## Development

```sh
uv run ruff check .
uv run mypy src
uv run pytest
uv run python scripts/check_boundary.py
```

See [coding standards](CODING_STANDARDS.md) before changing the core.
