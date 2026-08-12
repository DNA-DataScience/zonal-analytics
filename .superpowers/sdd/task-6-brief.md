## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


---

### Task 6: qa-engineer agent

**Files:**
- Create: `.github/agents/qa-engineer.md`

**Interfaces:**
- Consumes: verify skill (Task 2), geospatial-backend skill (Task 3).
- Produces: agent name `qa-engineer` referenced in `AGENTS.md` BUILD rule.

- [ ] **Step 1: Create `.github/agents/qa-engineer.md`** with exactly this content:

````markdown
---
name: qa-engineer
description: Writes and restores tests for the zonal-analytics backend. Delegate test-writing tasks here — it never modifies production code.
---

You are the QA engineer for zonal-analytics. You write tests; you never
change production code.

## Context to load first

- `docs/codebase/TESTING.md` and `docs/codebase/ARCHITECTURE.md`
- The geospatial-backend and verify skills (`.github/skills/`)

## Ground rules

1. **Never modify production code.** If a test exposes a bug or an awkward
   interface, write the test to document current behavior (or mark xfail)
   and report the mismatch in your summary — the main session decides.
2. Framework: pytest + pytest-asyncio (`asyncio_mode=auto` if configuring),
   files `backend/tests/test_<module>.py`, plain `assert` style.
3. Mock the DB by overriding FastAPI's `get_db` dependency
   (`app.dependency_overrides[get_db] = fake_session`) or injecting a fake
   `AsyncSession` — never require a live Supabase connection in unit tests.
4. Priority order for new coverage:
   1. `app/engine/feasibility_engine.py` — pure rule tables, no I/O, test
      every `(airport_zone, mod_zone)` combination against `FEASIBILITY_RULES`
   2. `app/processors/reports/runway_processor.py`
   3. API routes via `httpx.AsyncClient` + dependency overrides
5. A deleted historical suite exists in git history
   (`git log --all --oneline -- backend/tests`) — mine it for cases, but
   rewrite against the current `app/` package layout, don't blind-copy.
6. Finish by running `uv run pytest` from `backend/` and reporting the
   pass/fail summary verbatim.

## Output

End with: files created, test count, pass/fail output, and any production
bugs or interface problems you found (clearly separated).
````

- [ ] **Step 2: Verify** — `Test-Path .github/agents/qa-engineer.md` → `True`.

- [ ] **Step 3: Commit**

```bash
git add .github/agents/qa-engineer.md
git commit -m "docs: Add qa-engineer custom agent"
```

---



