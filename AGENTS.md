# operating-memory-public

Local Markdown-first memory core: notes are authoritative and SQLite is a derived store. Start with `README.md` and `docs/memory-core.md`.

This repo uses the AIL SDLC (`/grill` → `/spec` → `/ship`). Specs live in `docs/specs/`; locked acceptance tests live in `tests/acceptance/`. Run contract: `.sdlc.json`.

`scripts/check` is the verification command used locally, in CI, and by the Stop hook.

- Domain words: `CONTEXT.md`
- Review rules: `CODING_STANDARDS.md`
- Existing type debt: `.basedpyright/baseline.json`
- Black-box test style to copy: `tests/test_cli.py`
