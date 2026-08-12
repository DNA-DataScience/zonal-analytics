# Task 7 Report: frontend-dev agent

## Summary
Created `.github/agents/frontend-dev.md` with the exact content specified in
`task-7-brief.md` (Step 1), containing YAML frontmatter (`name: frontend-dev`,
description) followed by the agent instructions body covering: context to
load first (STRUCTURE.md, CONVENTIONS.md, map-ui/verify skills), 7 ground
rules (IControl pattern, Layerer.tsx wiring, API base URL config extraction,
`@/` import alias, `trackEvent` analytics, dependency flagging, lint/build
gate), and an output section requiring a plain-language summary.

## Steps performed
1. **Create file** — `.github/agents/frontend-dev.md` created verbatim from
   the brief (fenced block content only, frontmatter preserved).
2. **Verify** — `Test-Path .github/agents/frontend-dev.md` → `True`.
3. **Commit** — `git add .github/agents/frontend-dev.md` then
   `git commit -m "docs: Add frontend-dev custom agent"`.
   Commit: `12f7ba6dd7393d7e6623a5971b10f4ec4433d4a8`
   (1 file changed, 33 insertions(+)).

## Self-review
Compared committed file content (`git show HEAD:.github/agents/frontend-dev.md`)
against the brief's fenced block content — byte-for-byte match, no diff
output. Commit message matches the exact required string, single line, no
body, no trailers, no Co-authored-by (per Global Constraints for this plan's
commits).

## Concerns
None. File was created and committed exactly as specified; branch remains
`agenting` (no branch switch performed).
