## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


---

### Task 5: walkthrough skill + learning log seed

**Files:**
- Create: `.github/skills/walkthrough/SKILL.md`
- Create: `docs/superpowers/walkthroughs.md`

**Interfaces:**
- Consumes: walkthrough mandate in `AGENTS.md` step 5 (Task 1).
- Produces: `docs/superpowers/walkthroughs.md` log format used by every future walkthrough.

- [ ] **Step 1: Create `.github/skills/walkthrough/SKILL.md`** with exactly this content:

````markdown
---
name: walkthrough
description: Mandatory post-implementation learning review with the user. Run after completing any plan (or significant change) so the user understands what was built and the git operations used. Use when asked to review, explain, or walk through completed work.
---

# Walkthrough — Learning Review

Purpose: the user must be able to explain every change merged into this repo.
Run this interactively — it is a conversation, not a report dump.

## Process (in order)

1. **Tour** — summarize what changed file-by-file, in dependency order
   (data → backend API → frontend UI). For each file: what changed and *why*,
   2-4 plain sentences. No jargon without a one-line definition.

2. **Deep-dive Q&A** — ask the user which file or concept they want to dig
   into. Show the actual code and explain it. Repeat until they're done.

3. **Comprehension check** — ask the user 2-3 concrete questions about the
   change (e.g. "what happens if this query returns NULL?"). Wrong or unsure
   answers become friendly explanations — never judgments. Use the ask_user
   tool, one question at a time.

4. **Git recap** — list the git commands used during the work, in order, and
   explain why each was chosen (e.g. merge vs rebase). Keep it to the commands
   that actually taught something.

5. **Log** — append a short entry to `docs/superpowers/walkthroughs.md`:

```markdown
## YYYY-MM-DD — <topic>
- Changed: <one-line summary of the change>
- Learned: <concepts the user asked about or missed in the check>
- Git: <commands covered>
```

Commit the log update: `docs: Log walkthrough for <topic>`.
````

- [ ] **Step 2: Create `docs/superpowers/walkthroughs.md`** with exactly this content:

````markdown
# Walkthrough Log

Learning history from post-implementation reviews. Newest entries first.
Format per entry: Changed / Learned / Git (see the walkthrough skill).
````

- [ ] **Step 3: Verify** — both files exist (`Test-Path` → `True` for each).

- [ ] **Step 4: Commit**

```bash
git add .github/skills/walkthrough docs/superpowers/walkthroughs.md
git commit -m "docs: Add walkthrough skill and learning log"
```

---



