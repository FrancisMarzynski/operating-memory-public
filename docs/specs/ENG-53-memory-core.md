# ENG-53 — Generic Memory Core

## Problem Statement

Operating Memory needs a reusable core that lets an adopter derive a queryable
memory database from a folder of Markdown notes. The current source system
demonstrates useful capabilities, but its folder layout, entity taxonomy,
names, examples, credentials, historical records, and UI are private evidence,
not a product dependency. A stranger must be able to use this repository
without discovering that source system or conforming to its conventions.

## Solution

Ship a small Python-first core with three explicit boundaries:

1. A versioned, repository-local TOML configuration declares the adopter's
   note roots, entity kinds, and optional decision/journal discovery rules.
2. A deterministic importer reads only files selected by that configuration,
   produces a dry-run report by default, and writes a generic relational model
   only after an explicit apply flag.
3. A CLI reads the imported generic model through a narrow repository API. It
   never derives filesystem paths, entity kinds, or organisational terminology
   from code defaults.

The first vertical slice is intentionally local and testable: SQLite is the
reference backend. Supabase adapters, Edge Functions, API authentication,
semantic retrieval, UI, and any migration of private data are separate work.

## User Stories

1. As an adopter, I want to declare my own entity kinds so that the core does
   not impose another organisation's taxonomy.
2. As an adopter, I want to map my Markdown files with relative glob patterns
   so that I can retain my existing note layout.
3. As an adopter, I want imports to reject paths outside the configured notes
   root so that an accidental configuration cannot read unrelated files.
4. As an adopter, I want an explicit configuration version so that upgrades
   can fail clearly rather than reinterpret my notes silently.
5. As an adopter, I want a dry-run report before any database mutation so that
   I can inspect the import scope.
6. As an adopter, I want deterministic record identities so that repeated
   imports update the same records.
7. As an adopter, I want a structured import result so that scripts can report
   discovered, created, updated, unchanged, and skipped records.
8. As an adopter, I want generic entity records with a kind, stable key,
   title, source path, and body so that notes remain the durable authority.
9. As an adopter, I want optional decision-log parsing with a declared line
   format so that I can import a ledger without adopting a hidden convention.
10. As an adopter, I want decision records linked to their configured entity
    so that I can retrieve the reasons behind current state.
11. As an adopter, I want optional journal discovery configured separately
    from entities so that chronological notes are not misclassified as state.
12. As an adopter, I want imports to report malformed optional records without
    corrupting successfully parsed records.
13. As an adopter, I want the CLI to list entity kinds and retrieve an entity
    by kind and key so that core retrieval works without a UI or network API.
14. As an adopter, I want the CLI to show an entity with its imported decisions
    so that current state and its rationale can be inspected together.
15. As a contributor, I want committed fixtures to be invented and generic so
    that tests demonstrate behaviour without exposing private material.
16. As a reviewer, I want an automated repository scan that rejects banned
    private identifiers and paths so that the extraction boundary is enforced.
17. As a future adapter author, I want documented interfaces and an example
    configuration so that I can add a hosted backend or API without changing
    import semantics.

## Implementation Decisions

- Python 3.11+ is the initial runtime. Package metadata uses standard
  `pyproject.toml`; runtime configuration uses TOML parsed with `tomllib`.
- The public configuration file is `operating-memory.toml`. It has a required
  `version = 1`, a notes-root path, a non-empty declared `entity_kinds` list,
  and one or more entity import rules. There are no implicit roots or default
  kinds.
- An entity import rule declares: `kind`, `glob`, `key_from` (`path` for this
  slice), and an optional `title_from` (`first_heading` or filename). Paths are
  relative to the configured notes root and must resolve beneath it.
- Optional decision-log rules are attached to an entity rule and declare a safe
  per-note relative `path_template` containing exactly one `{note_stem}`
  placeholder, ensuring one unambiguous log per entity. They use the only
  supported v1 grammar:
  `YYYY-MM-DD — free-form decision body`. Invalid lines are reported as
  skips, not silently interpreted.
- Optional journal rules declare their own glob and date extraction pattern.
  Journal import is independent of entity import and has no assumed personal
  directory or subject.
- The domain model uses generic names only: `Entity`, `Decision`, `JournalEntry`,
  `ImportPlan`, `ImportReport`, and `MemoryStore`. No source taxonomy appears
  in code, tests, config, documentation, or command names.
- The v1 storage contract is SQLite via the `MemoryStore` interface. The schema
  stores source-relative paths and content hashes; it does not copy directory
  structure into columns or infer meaning from a path.
- Imports are idempotent. Identity is a stable hash of the configured kind and
  source-relative path; decisions are a stable hash of entity identity, date,
  and body. The importer upserts records and reports unchanged content.
- CLI commands are `om config validate`, `om import --dry-run`, `om import
  --apply`, `om kinds`, `om entity get <kind> <key>`, and `om decisions <kind>
  <key>`. The CLI requires explicit `--config` and `--database` arguments in
  v1; environment variables are not an alternate configuration channel.
- Every mutating command requires `--apply`; `om import` with no mode fails
  closed. A dry run opens no writable database connection.
- Error messages identify the configuration field or source-relative file that
  failed, never print file content by default.
- Documentation includes an invented `example-notes/` corpus and matching
  TOML. It must not mention, reproduce, or resemble private operating data.
- A repository boundary check rejects known private product names, path roots,
  identifiers, and UI assets. It is a regression guard, not a replacement for
  review.

## Testing Decisions

- Tests exercise observable behaviour through configuration loading, import
  planning/application, SQLite query results, and CLI exit/output contracts;
  they do not assert private implementation helpers.
- Fixtures cover a custom two-kind taxonomy, nested note paths, successful
  dry run, apply, idempotent re-import, changed-note update, valid decision
  import, malformed decision skip, invalid configuration, path escape, and
  CLI retrieval.
- Tests prove no-write dry runs by asserting that no database file is created.
- Boundary tests scan tracked repository content, excluding `.git`, virtual
  environments, and build output, for prohibited private references.
- The suite runs with the standard library plus the selected test runner;
  formatter/linter/type-checker choices are documented in project tooling and
  run in CI before review.

## Out of Scope

- Supabase/Postgres schema and migrations, Deno/Edge Functions, hosted API,
  authentication, browser/UI code, semantic search, external integrations,
  remote synchronization, automatic config generation, and any data migration.
- Supporting every Markdown front-matter convention, custom parser plug-ins,
  destructive reconciliation/deletion, or arbitrary decision grammars.
- Importing any source repository history, private material, credentials,
  production exports, screenshots, fixtures, or client data.

## Further Notes

- Legacy code may be inspected only after this contract is fixed, solely to
  identify generic capability parity. It is not copied, vendored, executed
  against private data, or used as a source of names, defaults, fixtures, or
  documentation.
- Public release remains blocked independently by ENG-51, ENG-61, design gate,
  test coverage, and CI. ENG-53 may move to In Review only after the private
  repository passes its own spec, boundary, and independent-review gates.
