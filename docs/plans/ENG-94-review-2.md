# ENG-94 review — attempt 2

## Spec

### User stories

- **PASS — YAML frontmatter titles.** `_title()` checks whether the first
  body line is exactly `---`, finds the next exact `---`, and begins the
  existing heading scan after it. The added importer test obtains `Real
  Heading` from a frontmatter-prefixed note.
- **PASS — exclusions omit template/archive paths.** Both entity and journal
  discovery call `_is_excluded()` before attempting to read a path, so an
  excluded path cannot become either a record or a skip. `_glob_matches()`
  handles path components and recursive `**`; the revised test covers a
  nested `projects/_TEMPLATE/nested/overview.md` against
  `projects/_TEMPLATE/**`, and direct matcher verification also confirms the
  required `**/_TEMPLATE/**` pattern matches nested descendants.
- **PASS — fixed-name sibling decision logs.** Configuration now permits zero
  `{note_stem}` instances while retaining the rejection of two instances and
  remaining brace placeholders. The existing resolution expression joins the
  template to `path.parent`, and the added integration test imports
  `Decision Log.md` beside `atlas.md`.

### Validation contract / seams

1. **PASS — frontmatter then H1.** The added test verifies a real ATX heading
   after a closed YAML block yields `Real Heading`.
2. **PASS — unterminated frontmatter.** If `lines.index("---", 1)` raises
   `ValueError`, `start` remains zero; the added test verifies the existing
   filename fallback with no exception or hang.
3. **PASS — no-frontmatter behaviour and setext.** `start` defaults to zero,
   leaving the pre-existing scan intact. The existing
   `test_first_heading_supports_markdown_headings_and_skips_code_fences`
   continues to verify the setext case.
4. **PASS — excluded entries and skips.** Entity and journal exclusions are
   applied before all parse/read skip paths. The focused test asserts that the
   nested excluded entity and archived journal are absent from records and
   skipped output.
5. **PASS — no exclusion preserves prior plans.** `exclude` defaults to `()`
   on both rules and `any(... for pattern in ())` is false. Existing importer
   plan tests use configuration without `exclude` and retain their prior exact
   entity, decision, journal, and skip expectations.
6. **PASS — unsafe exclusion validation.** Every item is passed through
   `_safe_relative()` with the supplied `entities[0].exclude` or
   `journals[0].exclude` field name. Tests cover an absolute entity pattern
   and a journal pattern containing `..`.
7. **PASS — fixed sibling decision import.** The new importer test writes
   `Decision Log.md`, then checks its line's body and source path in the plan.
8. **PASS — per-note decision compatibility.** A single `{note_stem}` is
   still accepted and replaced during log resolution; existing per-note log
   tests exercise that path.
9. **PASS — invalid decision placeholders.** The count guard rejects two
   `{note_stem}` placeholders, and braces remaining after replacement reject
   unknown/malformed placeholders. Focused config tests cover both cases.

Required documentation was updated in `README.md` and `docs/memory-core.md`
for `exclude` and fixed-name sibling decision logs. The diff leaves journal
date handling and `apply_plan` unchanged, so it introduces no out-of-scope
behaviour. The private-vault acceptance assertion belongs in the PR description
and cannot be verified from this checkout.

Verification: `PYTHONPATH=src python3 -m unittest discover -s tests -v` passed
(36 tests); `python3 scripts/check_boundary.py` passed. The required `uv run
ruff check .`, `uv run mypy src`, and `uv run pytest` could not be run because
the environment has no `uv` executable (and its Python environment lacks those
three modules).

## Standards

None found. The custom component-aware glob matcher is directly required to
make notes-root-relative recursive exclusion patterns (notably
`**/_TEMPLATE/**`) work correctly; its local cache prevents repeated recursive
states rather than introducing speculative abstraction. The small additions to
the config dataclasses and the two existing discovery loops are cohesive with
their respective responsibilities, with no Fowler smell from the supplied
baseline.
