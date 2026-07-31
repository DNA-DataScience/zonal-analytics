## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


---

### Task 2: verify skill

**Files:**
- Create: `.github/skills/verify/SKILL.md`

**Interfaces:**
- Consumes: gate commands named in `AGENTS.md` (Task 1).
- Produces: the "definition of done" referenced by both agents (Tasks 6–7).

- [ ] **Step 1: Create `.github/skills/verify/SKILL.md`** with exactly this content:

````markdown
---
name: verify
description: Definition of done for zonal-analytics. Run before claiming any task, fix, or plan step complete. Use whenever asked to verify, check, or finish work.
---

# Verify — Definition of Done

Run every gate that applies to what changed. All must pass. Never claim
completion without pasting the actual command output.

## Backend gates (anything under `backend/`)

```powershell
cd backend
uv run pytest
```

- Expected: exit code 0. NOTE: until the test suite is restored (queued
  stabilization plan), pytest collects nothing — that counts as pass, but say so.
- Import smoke check when pytest collects nothing:
  `uv run python -c "import app.main"` — expect no output, exit 0.

## Frontend gates (anything under `frontend/`)

```powershell
cd frontend
npm run lint
npm run build
```

- Expected: lint exits 0 (warnings allowed, errors not); build completes
  with "Compiled successfully".
- There is NO frontend test framework yet — lint + build are the only gates.

## Docs-only changes

No gates required beyond reading the rendered markdown once for broken
formatting.

## On failure

1. Read the full error before editing anything.
2. Fix, re-run the same gate, repeat until green.
3. If the failure is pre-existing and unrelated, report it to the user —
   do not silently skip the gate.
````

- [ ] **Step 2: Verify** — `Test-Path .github/skills/verify/SKILL.md` → `True`; frontmatter has `name` and `description` keys.

- [ ] **Step 3: Commit**

```bash
git add .github/skills/verify
git commit -m "docs: Add verify skill with definition of done"
```

---



