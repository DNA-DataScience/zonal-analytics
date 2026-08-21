# Task 2 Report: verify skill

## Files created
- `.github/skills/verify/SKILL.md` (new directories `.github/skills/verify/` created)

## Verification
```
PS> Test-Path .github\skills\verify\SKILL.md
True
PS> Get-Content .github\skills\verify\SKILL.md -TotalCount 5
---
name: verify
description: Definition of done for zonal-analytics. Run before claiming any task, fix, or plan step complete. Use whenever asked to verify, check, or finish work.
---
```
- `Test-Path` returns `True`.
- Frontmatter contains `name: verify` and `description: ...` keys as required.

## Self-review
Diffed the created file content against the brief's verbatim block (task-2-brief.md lines 26–71, inside the ` ```markdown ... ``` ` fence). Content matches exactly, including:
- YAML frontmatter (`name`, `description`)
- Heading `# Verify — Definition of Done`
- Backend gates section with `powershell` code block (`cd backend`, `uv run pytest`)
- Frontend gates section with `powershell` code block (`cd frontend`, `npm run lint`, `npm run build`)
- Docs-only changes section
- On failure numbered list
No deviations found.

## Commit
```
[agenting 7705b50] docs: Add verify skill with definition of done
 1 file changed, 45 insertions(+)
 create mode 100644 .github/skills/verify/SKILL.md
```
Commit hash: `7705b50c049e6d0eb15a371442f46d72ad3d2deb`
Commit message is single line, no body, no trailers — matches required format.

## Branch
Remained on `agenting` throughout; no branch switch performed.
