# Task 4 Report: map-ui skill

## Summary
Created `.github/skills/map-ui/SKILL.md` with the exact content specified in
`task-4-brief.md` (Step 1), verified its existence, and committed it per the
required single-line commit message format.

## Steps performed
1. Created directory `.github/skills/map-ui/`.
2. Created file `.github/skills/map-ui/SKILL.md` containing the YAML
   frontmatter (`name: map-ui`, `description: ...`) and full body (IControl
   anatomy example, API base URL, Layers, Analytics, Non-obvious constraints
   sections) copied verbatim from the brief.
3. Verified with `Test-Path .github\skills\map-ui\SKILL.md` → `True`.
4. Committed with `git add .github/skills/map-ui` and
   `git commit -m "docs: Add map-ui skill"`.

## Self-review
Viewed the created file end-to-end (67 lines) and compared line-by-line
against the brief's Step 1 content block (brief lines 25-90, excluding the
outer ```` markdown fence markers). Content matches verbatim, including the
em-dash in the frontmatter description, code fence language (`tsx`), and all
inline code spans/backticks.

## Verification
- `Test-Path .github\skills\map-ui\SKILL.md` → `True`
- `git commit` succeeded: 1 file changed, 66 insertions(+)

## Commit
- Hash: `f9eb3627f4ace44097a945d5fdd441b247336f58`
- Message: `docs: Add map-ui skill`
- Style: single line, no body, no trailers — compliant with global
  constraints.

## Concerns
None. No production code was touched; only a new skill doc file was added,
consistent with the plan's "No production code changes in this plan"
constraint.
