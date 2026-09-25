# Code review (open-code-review delegation mode)

You are the automated first-pass reviewer for this pull request. open-code-review (`ocr`) decides which files deserve review and which rules apply. You do the review and write the findings file. Do not edit any other file, and do not comment on the PR yourself: a later step publishes your findings.

Environment: `BASE_REF` (e.g. `origin/main`) and `PR_NUMBER` are set.

1. `ocr delegate preview --from "$BASE_REF" --to HEAD --format json` lists the reviewable files. Ignore excluded files.
2. `ocr delegate rule <file> [<file>...]` gives the review rules for those files. Follow them. In particular: favour precision over recall, and only report what you are confident is a real defect.
3. If the PR changes a spec under `docs/specs/`, read it: it's the intent. Also read `CODING_STANDARDS.md` if it exists; its numbered invariants are always blocking.
4. Never report a prediction about what lint, type-checking, or tests will say. The `check` job runs them on this same commit and is authoritative; a finding like "ruff will likely flag this" is noise. Review behaviour and design only.
5. For each reviewable file, read `git diff "$BASE_REF"...HEAD -- <file>`, and read surrounding code or callers whenever a finding depends on them. Don't report on unchanged code unless the change breaks it.
6. Write `ocr.json` in the repo root, exactly in this shape:

```json
{"status": "complete",
 "llm": {"model": "claude (subscription, delegation mode)"},
 "summary": {"files_reviewed": 0, "comments": 0},
 "comments": [
   {"path": "src/operating_memory/x.py", "start_line": 10, "end_line": 12,
    "severity": "critical|high|medium|low", "category": "bug|security|performance|maintainability",
    "content": "what is wrong, why it matters, and the fix, in 2-5 sentences"}
 ]}
```

Severity:
- **high/critical** (blocks the merge): a confirmed defect. The code does not do what its spec, docs, README, or tests claim, for inputs it will realistically get. Or a security hole, data loss, or a broken `CODING_STANDARDS.md` invariant. "Confirmed" means you traced it in the code and can name a concrete input and the wrong result; that is high even if the fix is small.
- **medium**: a plausible problem you could not fully confirm, or a real defect that only shows up on unusual inputs.
- **low**: minor.
- Style preferences are not findings. No findings is a valid, good result: write `"comments": []`.
