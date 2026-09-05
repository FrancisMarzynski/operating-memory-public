# Operating Memory

[![CI](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml/badge.svg)](https://github.com/FrancisMarzynski/operating-memory-public/actions/workflows/ci.yml)

Operating Memory turns a folder of ordinary Markdown notes into a local,
queryable memory store—without moving the notes into a proprietary database.

Use it when a project, team, or agent needs to answer questions such as:

- What projects or reference records do we have?
- What decisions were made about this project, and when?

Your Markdown remains the source of truth. Operating Memory imports it into a
local SQLite file so a CLI or another application can retrieve structured
answers quickly. Re-import whenever notes change; the same source records keep
the same identities, so imports are idempotent.

It is deliberately not a note-taking app, a hosted knowledge base, or an AI
agent framework. It is the small local memory layer those tools can build on.

## Memory model

The source records are ordinary Markdown files:

- **Entities** describe durable things, such as a project or reference.
- **Decisions** are append-only dated lines associated with an entity. The
  line format is declared in configuration, so your own decision-log
  convention works without changing code.
- **Journal entries** are dated Markdown files for temporal records.

The database is derived data, never a replacement for those notes. Record
identities are deterministic: they use kind and source-relative location, with
decision date and body included where needed.

This repository is a deliberately small, generalised public extraction of a
larger private operating-memory system. The private system is demonstrated live
rather than shared; its architecture is described in
[the private-system architecture guide](docs/private-system-architecture.md)
without exposing its data, configuration, or integrations.

## See it work

The repository includes a small invented note corpus. From a fresh clone, run
these commands verbatim:

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

The final commands return structured records from the Markdown corpus:

```text
$ om --config operating-memory.example.toml --database /tmp/memory.sqlite kinds
project
reference

$ om --config operating-memory.example.toml --database /tmp/memory.sqlite entity get project projects/orbit.md
{"body":"# Orbit\\n\\nAn invented project note used to demonstrate a nested, generic import.\\n","key":"projects/orbit.md","kind":"project","source_path":"projects/orbit.md","title":"Orbit"}

$ om --config operating-memory.example.toml --database /tmp/memory.sqlite decisions project projects/orbit.md
[{"body":"Start with a local import.","date":"2026-03-10","source_path":"projects/orbit.decisions.log"}]
```

In other words: add or edit a Markdown project note, run `import --apply`, and
your tools can ask for that project or its decisions through the local database.

## Use it with your notes

Copy `operating-memory.example.toml` and make three choices: set `notes_root` to
your Markdown folder; declare the entity kinds you want to retrieve; and add an
`[[entities]]` rule for each folder or glob that contains them. Decision logs
and journals are optional import rules. The included configuration is the
smallest working example: it imports project notes from `projects/*.md` and
reference notes from `references/*.md`, relative to `notes_root`.

If your decision logs do not use the default
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
