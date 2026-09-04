# Coding standards

This is intentionally short. It records only rules surfaced by reviews of this
codebase; it is not a copy of another repository's policy.

- Keep Markdown authoritative. Imports are projections, so changes must retain
  deterministic identities and idempotent re-imports.
- Treat an import as one transaction. The storage lifetime owns schema setup,
  commit, rollback, and foreign-key enforcement.
- Validate configurable syntax at the boundary with field-named errors. Do not
  accept malformed templates or silently substitute a different meaning.
- Keep the repository interface narrow. Add a storage operation only when a
  caller needs a distinct persistence capability, not as a convenience wrapper.
- Preserve explicit CLI mutation modes. A command that changes storage must
  require an affirmative mode rather than inferring permission from invocation.
- Add focused tests at the changed seam and run the full repository checks
  before review.
