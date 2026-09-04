# Private-system architecture

The public package is a small, generalised extraction from a larger private
operating-memory system. The private system is demonstrated live rather than
shared. This document describes its mechanisms, not its data, configuration,
or connected accounts.

## End-to-end shape

```text
Markdown vault (authoritative records)
        |
        v
Importer --> database projection --> retrieval command-line interface
                                      |
                                      v
                              application workspace
                                      ^
                                      |
                    issue tracker, calendar, and workspace connectors
```

The vault remains the source of truth. An importer turns its structured
Markdown into a queryable database projection. A retrieval CLI and application
layer read that projection while retaining links back to the authoritative
records. Connectors provide current work, calendar reality, and workspace
context without making any external system the canonical record.

## Record layers

The system keeps three distinct layers because each answers a different
question:

- A **current-state artifact** says what is true now.
- An append-only **reasoning ledger** records decisions, alternatives, and why
  state changed.
- A **raw source** preserves the underlying material when exact evidence is
  needed.

This separation prevents a current summary from becoming an unreadable history,
while keeping a decision trace and its evidence recoverable.

## Write safety during migration

Decisions use an append-only ledger. When a decision is written through the
application path, a write-once identity marker is recorded with its Markdown
line. The importer recognises that marker and reuses the same identity instead
of creating a second record through the import path.

During migration, a dual-write bridge updates the authoritative Markdown and
the database-facing operating memory in the same action. The marker and
idempotent import are the guardrails that keep those paths convergent until a
record type can safely move to one write path.

## Autonomous execution loop

The private system also runs a bounded autonomous loop:

```text
labelled ticket
  -> execution agent
  -> load relevant context from the operating memory
  -> perform the scoped work
  -> commit the resulting vault changes
  -> move the ticket to review
```

The label selects a deliberately scoped run; it does not grant open-ended
authority. The context load makes the agent work from durable operational state,
and the commit plus review transition leaves a verifiable trail for a human to
inspect.
