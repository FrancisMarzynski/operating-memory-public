# Coding standards

Read during review. Mechanical rules are enforced by `scripts/check`; the
rules below preserve boundaries that a tool cannot reliably judge.

## Invariants (blocking)

1. Keep Markdown authoritative. Imports are projections, so changes must retain
  deterministic identities and idempotent re-imports.
2. Treat an import as one transaction. The storage lifetime owns schema setup,
  commit, rollback, and foreign-key enforcement.
3. Validate configurable syntax at the boundary with field-named errors. Do not
  accept malformed templates or silently substitute a different meaning.
4. Keep the repository interface narrow. Add a storage operation only when a
  caller needs a distinct persistence capability, not as a convenience wrapper.
5. Preserve explicit CLI mutation modes. A command that changes storage must
  require an affirmative mode rather than inferring permission from invocation.
6. Preserve the public extraction boundary enforced by `scripts/check_boundary.py`.
   Do not commit private notes, configuration, or integrations.

## Judgement

- Add focused tests at the changed seam and run `scripts/check` before review.
- Prefer black-box CLI tests following `tests/test_cli.py` when behavior is visible there.
