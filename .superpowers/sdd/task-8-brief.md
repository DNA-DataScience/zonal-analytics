## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


---

### Task 8: Git migration — agenting → dev (INLINE WITH USER ONLY)

**Files:** none created — branch operations only.

**Interfaces:**
- Consumes: all Task 1–7 commits (must be on `agenting` before rename).
- Produces: `dev` branch that all future `feat/*`/`fix/*` work branches from.

**What you'll learn:** reading divergence between branches, merge vs rebase,
renaming a branch locally and on the remote, branch protection.

- [ ] **Step 1: Inspect the divergence (lesson first, action second)**

```bash
git fetch origin
git log --oneline agenting..origin/main   # commits main has that we lack
git log --oneline origin/main..agenting   # commits we have that main lacks
```

Walk the user through what each list means before proceeding.

- [ ] **Step 2: Merge main into agenting**

```bash
git merge origin/main
```

Expected: merge commit, or conflicts. If conflicts: resolve them *together
with the user*, explaining each conflict marker. Then verify the app still
imports: `cd backend; uv run python -c "import app.main"` and
`cd frontend; npm run build`.

- [ ] **Step 3: Rename to dev and push**

```bash
git branch -m agenting dev
git push -u origin dev
```

Expected: `dev` tracking `origin/dev`.

- [ ] **Step 4: Retire the old remote branch (after user confirms)**

```bash
git push origin --delete agenting
```

- [ ] **Step 5: Manual GitHub steps (user does these in the browser, guided)**

1. Repo Settings → General → Default branch: consider setting to `dev`
2. Settings → Branches → Add branch protection rule for `main`:
   require a pull request before merging (CI check requirement comes later,
   once CI exists)
3. Review stale branches `suzman6-*` on GitHub — delete merged ones

- [ ] **Step 6: Confirm final state**

```bash
git branch -a
git status -sb
```

Expected: local `dev` tracking `origin/dev`; no local `agenting`.

---



