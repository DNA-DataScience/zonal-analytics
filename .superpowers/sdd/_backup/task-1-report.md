# Task 1 Report — AGENTS.md + IDE pointer

## Files created

1. `AGENTS.md` (repo root) — canonical agent instructions, 37 content lines.
2. `.github\copilot-instructions.md` — pointer file to `AGENTS.md`.

Both created with the exact content specified in
`.superpowers\sdd\task-1-brief.md` (fences stripped, content copied verbatim).

## Verification output

```
> Get-Content AGENTS.md | Measure-Object -Line
Lines Words Characters Property
----- ----- ---------- --------
   37

> Test-Path .github\copilot-instructions.md
True
```

- `AGENTS.md` line count: 37 (well under the ≤65 / "under ~60 content lines" requirement).
- `.github\copilot-instructions.md` exists: `True`.

## Self-review result

Compared the created files against the brief's fenced blocks line-by-line
(headings, bullet text, code samples, skill names `geospatial-backend`,
`map-ui`, `verify`, `walkthrough`, `qa-engineer`, `frontend-dev`). Content
matches verbatim — no additions, omissions, or formatting drift. `git show
HEAD --stat` confirms exactly 2 files changed, 53 insertions, 0 deletions,
consistent with two newly-created files and no unintended modifications.

## Commit

- Message: `docs: Add AGENTS.md as canonical agent instructions`
  (single line, no body, no trailers — matches Global Constraints commit
  style and the exact message given in the brief).
- Commit hash: `2d06c3c7caa2eb26117ff4f5d1e80d5439e3fe1e`
- Branch: `agenting` (work done in place, no branch switch).

## Notes

Untracked `.idea/` and `.superpowers/` directories are pre-existing in the
working tree and were intentionally left out of this commit (only
`AGENTS.md` and `.github/copilot-instructions.md` were staged, per the
brief's Step 4 `git add` command).
