# ENG-94 review — attempt 1

## Spec

### User stories

- **PASS — YAML frontmatter titles.** `_title()` now detects an exact opening
  `---`, advances past the next exact delimiter, then performs the existing
  heading scan. The added importer test proves the reported real ATX heading.
- **FAIL — exclusions reliably omit template/archive paths.** The matcher is
  `Path(relative).match(pattern)`. This is not equivalent to the recursive glob
  matching used for rule discovery: on Python 3.11,
  `Path("01-Agency/Clients/_TEMPLATE/nested/Overview.md").match("**/_TEMPLATE/**")`
  is false. Thus a descendant within a `_TEMPLATE` directory is imported even
  with the acceptance-check pattern `exclude = ["**/_TEMPLATE/**"]`. It also
  makes an unanchored `"*.md"` exclusion match nested files, unlike the
  notes-root-relative discovery glob. Use one consistent, recursive,
  notes-root-relative glob matcher and add coverage for nested descendants.
- **PASS — fixed-name sibling decision logs.** Config permits zero
  `{note_stem}` instances while still rejecting more than one or any remaining
  brace placeholder. The existing `path.parent / template.replace(...)`
  resolution correctly finds `Decision Log.md` alongside the source note.

### Validation contract / seams

1. **PASS — frontmatter then H1.** The added test obtains `Real Heading` from
   frontmatter followed by `# Real Heading`.
2. **PASS — unterminated frontmatter fallback.** `ValueError` from locating a
   closing delimiter leaves `start` at zero; the focused test verifies the
   existing filename fallback and no exception.
3. **PASS — no-frontmatter behaviour, including setext.** The pre-existing
   `test_first_heading_supports_markdown_headings_and_skips_code_fences` still
   exercises a setext heading; the new `start = 0` default preserves that scan.
4. **FAIL — excluded plan entries/skips.** The supplied test covers only a
   single immediate child of the excluded directory. It misses the recursive
   `**` defect above, so the claimed omission is not true for all paths matching
   the configured glob.
5. **PASS — omitted exclude preserves the plan.** `exclude` defaults to `()` on
   both rule dataclasses and `_is_excluded(..., ())` is false, leaving the prior
   discovery/read/plan path unchanged. This is not separately regression-tested,
   but it is directly established by the implementation and existing no-exclude
   importer tests.
6. **PASS — unsafe exclude validation.** Entity and journal exclusions call
   `_optional_safe_relative_list()`, which delegates each string to
   `_safe_relative()` and reports the passed field name. Tests cover both an
   absolute entity pattern and a `..` journal pattern.
7. **PASS — fixed sibling decision import.** The added importer test writes
   `Decision Log.md` beside `atlas.md` and imports its one line with the expected
   body and source path.
8. **PASS — existing per-note template compatibility.** A single
   `{note_stem}` remains accepted and is still replaced before the log is read;
   existing per-note decision tests exercise this behavior.
9. **PASS — invalid decision placeholders.** The count check rejects two
   `{note_stem}` instances, while the remaining-braces check rejects unknown
   placeholders; focused tests cover both cases.

Documentation for `exclude`, fixed sibling decision logs, and frontmatter title
handling was added to both required files. No scope creep affecting journal date
handling or `apply_plan` was found. The requested real-vault PR-description
statement is not represented in the repository diff and cannot be verified here.

Repository verification available in this checkout: `PYTHONPATH=src python3 -m
unittest discover -s tests -v` passed (36 tests), and `python3
scripts/check_boundary.py` passed. The mandated `uv run ruff check .`, `uv run
mypy src`, and `uv run pytest` could not be run because `uv` is absent from the
environment.

## Standards

None found. The changes are small, cohesive extensions of the configuration and
import-plan seams; they do not introduce a Fowler smell from the supplied
baseline. The exclusion defect above is a correctness issue, not a refactoring
smell.
