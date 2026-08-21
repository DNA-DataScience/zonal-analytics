## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


---

### Task 9: Dry-run validation + walkthrough

**Files:** none.

- [ ] **Step 1: Structural check**

```powershell
Test-Path AGENTS.md, .github/copilot-instructions.md,
  .github/agents/qa-engineer.md, .github/agents/frontend-dev.md,
  .github/skills/verify/SKILL.md, .github/skills/geospatial-backend/SKILL.md,
  .github/skills/map-ui/SKILL.md, .github/skills/walkthrough/SKILL.md,
  docs/superpowers/walkthroughs.md
```

Expected: nine `True` lines.

- [ ] **Step 2: Fresh-session dry run (user does this)**

User starts a new Copilot CLI session in the repo and asks: "what are the
workflow rules here?" — the answer should reflect AGENTS.md. Then asks it to
list available skills/agents — the four skills and two agents should appear.
If anything fails to load, fix paths/frontmatter and repeat.

- [ ] **Step 3: Run the walkthrough skill on this very plan**

First real use of the walkthrough: tour the created files, Q&A, comprehension
check, git recap of the Task 8 migration, and log the entry to
`docs/superpowers/walkthroughs.md`.

- [ ] **Step 4: Commit anything the dry run changed**

```bash
git add -A
git commit -m "docs: Log walkthrough for copilot dev structure"
```


