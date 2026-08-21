# Copilot Development Structure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the repo-level agent structure (AGENTS.md, 4 skills, 2 custom agents) and migrate git to the dev/main branching model, per the approved spec at `docs/superpowers/specs/2026-07-08-copilot-dev-structure-design.md`.

**Architecture:** Root `AGENTS.md` is the canonical always-on brief (cross-tool standard); `.github/copilot-instructions.md` is a thin pointer to it. Deep domain knowledge lives in four on-demand skills under `.github/skills/`. Two custom agents under `.github/agents/` handle delegated test-writing and frontend work. Git migration renames `agenting` → `dev` after syncing with `main`.

**Tech Stack:** Markdown config files only (no code changes). Git for the migration.

## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.

---

### Task 1: AGENTS.md + IDE pointer

**Files:**
- Create: `AGENTS.md`
- Create: `.github/copilot-instructions.md`

**Interfaces:**
- Produces: the workflow rules and skill/agent names (`geospatial-backend`, `map-ui`, `verify`, `walkthrough`, `qa-engineer`, `frontend-dev`) that Tasks 2–7 must match exactly.

- [ ] **Step 1: Create `AGENTS.md`** with exactly this content:

````markdown
# Zonal Analytics — Agent Instructions

Geospatial feasibility tool for wind-turbine siting in India (Suzlon).
Monorepo:

- `backend/` — FastAPI, Python 3.13, managed with **uv**. Raw SQL via async
  SQLAlchemy/asyncpg against Supabase Postgres schema `"GisDB"` (PostGIS).
  No ORM models, no migrations (tables created at startup lifespan).
- `frontend/` — Next.js 15 + React 19 + MapLibre GL 5, managed with **npm**.
  Map widgets are MapLibre `IControl` classes in `src/app/components/`.

## Knowledge base

Read `docs/codebase/` (STACK, STRUCTURE, ARCHITECTURE, CONVENTIONS,
INTEGRATIONS, TESTING, CONCERNS) before any non-trivial work.

## Commands

- Backend (from `backend/`): `uv sync` · dev: `uv run uvicorn app.main:app --reload` · tests: `uv run pytest`
- Frontend (from `frontend/`): `npm ci` · dev: `npm run dev` · gates: `npm run lint`, `npm run build`

## Workflow (hard rules)

Every non-trivial change follows SPEC → PLAN → BUILD → VERIFY → WALKTHROUGH:

1. **SPEC** — brainstorming skill → `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
2. **PLAN** — writing-plans skill → `docs/superpowers/plans/`; plain language,
   each phase carries a "What you'll learn" note
3. **BUILD** — step by step; TDD where tests exist; test-writing may be
   delegated to the `qa-engineer` agent, UI tasks to the `frontend-dev` agent
4. **VERIFY** — run the `verify` skill gates; must pass before claiming done
5. **WALKTHROUGH** — run the `walkthrough` skill with the user (mandatory)

Trivial changes (typos, one-liners) may skip 1–2 but never 4.
Specs and plans must be readable by a non-expert cold in six months:
no jargon dumps, explain the *why* of each decision.

## Git

- Work on `feat/<topic>` or `fix/<topic>` branched off `dev`; PR into `dev`.
- Promote `dev → main` via PR only when deploy-ready. `main` is deploy-only.
- Commits: **single line only** — `<type>: <Capitalized imperative subject>`,
  types `feat|fix|chore|docs|test|refactor`, ≤72 chars, no issue numbers,
  no body, no trailers.

## Repo skills (`.github/skills/`)

- `geospatial-backend` — GisDB schema, MVT tiles, add-a-layer recipe
- `map-ui` — IControl anatomy, Map.tsx registration, analytics events
- `verify` — definition of done + exact gate commands
- `walkthrough` — post-plan learning review with the user
````

- [ ] **Step 2: Create `.github/copilot-instructions.md`** with exactly this content:

````markdown
The canonical instructions for this repository are in the root `AGENTS.md`
file. Read and follow it.
````

- [ ] **Step 3: Verify**

Run: `Get-Content AGENTS.md | Measure-Object -Line` — expect ≤ 65 lines.
Run: `Test-Path .github/copilot-instructions.md` — expect `True`.

- [ ] **Step 4: Commit**

```bash
git add AGENTS.md .github/copilot-instructions.md
git commit -m "docs: Add AGENTS.md as canonical agent instructions"
```

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

### Task 3: geospatial-backend skill

**Files:**
- Create: `.github/skills/geospatial-backend/SKILL.md`

**Interfaces:**
- Produces: the add-a-layer recipe referenced by `qa-engineer`/`frontend-dev` agents and future feature plans.

- [ ] **Step 1: Create `.github/skills/geospatial-backend/SKILL.md`** with exactly this content:

````markdown
---
name: geospatial-backend
description: Backend patterns for zonal-analytics — GisDB schema, raw SQL conventions, MVT tile endpoints, feasibility engine, and the end-to-end recipe for adding a new map layer. Use for any backend/ or database task.
---

# Geospatial Backend Patterns

## Database

Supabase Postgres, schema `"GisDB"` (quoted, case-sensitive), PostGIS enabled.
Access is **raw SQL** through async SQLAlchemy (`sqlalchemy.text`) — no ORM
models. Session via `Depends(get_db)` from `app/db/connect_db.py`.
Pool is tiny (size 5 + overflow 5): guard heavy endpoints with an
`asyncio.Semaphore` (see `TILE_SEMAPHORE = asyncio.Semaphore(5)` in
`app/api/tiles.py`).

Known tables (all geometry stored as `geom3857`, EPSG:3857):

| Table | Key columns |
|-------|-------------|
| `"GisDB".airport_layers` | zone, name, type, radio, elevation, latitude, longitude, geom3857 |
| `"GisDB".mod_layers` | zone, name, type, geom3857 |
| `"GisDB".reserve_forests` | "Name", geom3857 |

Analytics/feedback tables are created at startup in `app/main.py` lifespan —
there is no migration tool. New tables follow that pattern until Alembic is
adopted (queued stabilization work).

## MVT tile endpoint template

Copy the pattern in `app/api/tiles.py`:

```python
QUERY = text("""
SELECT ST_AsMVT(tile, '<layer_name>', 4096, 'geometry') as mvt
FROM (
  SELECT <columns>,
  ST_AsMVTGeom(geom3857, ST_TileEnvelope(:z, :x, :y), 4096, 256, true) AS geometry
  FROM "GisDB".<table>
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")
```

Route shape: `GET /tiles/<layer>/{z}/{x}/{y}.mvt`, return 204 above
`MAX_ZOOM = 15`, empty MVT bytes when no data, semaphore-guarded.

## Feasibility engine

`app/engine/feasibility_engine.py` is config-as-data: `LAYER_CONFIG` declares
each layer (db_table, priority_order, query_fields, special_handlers);
`FEASIBILITY_RULES` maps `(airport_zone, mod_zone) → (feasibility, color)`.
Extend the tables — do not add branching logic.

## Recipe: add a new map layer end-to-end

1. Ingest data into a new `"GisDB"` table with a `geom3857` column + GiST index
2. Add MVT query + route in `app/api/tiles.py` (template above)
3. If it affects feasibility: add an entry to `LAYER_CONFIG` and extend
   `FEASIBILITY_RULES` in `app/engine/feasibility_engine.py`
4. Frontend: add source + layers in `frontend/src/app/lib/Layerer.tsx`
   pointing at the new tile route (see map-ui skill)
5. Run the verify skill gates

## Conventions

- Error handling: try/except per route, raise `HTTPException`; prefer
  `logging` over `print` in new code (analytics.py is the good example)
- Env vars in `backend/db.env` (gitignored): `user`, `password`, `host`,
  `port`, `dbname`; template at `backend/env-Template`
````

- [ ] **Step 2: Verify** — `Test-Path .github/skills/geospatial-backend/SKILL.md` → `True`.

- [ ] **Step 3: Commit**

```bash
git add .github/skills/geospatial-backend
git commit -m "docs: Add geospatial-backend skill"
```

---

### Task 4: map-ui skill

**Files:**
- Create: `.github/skills/map-ui/SKILL.md`

**Interfaces:**
- Produces: the IControl recipe consumed by the `frontend-dev` agent (Task 7).

- [ ] **Step 1: Create `.github/skills/map-ui/SKILL.md`** with exactly this content:

````markdown
---
name: map-ui
description: Frontend patterns for zonal-analytics — MapLibre IControl widgets, Map.tsx registration, layer wiring via Layerer.tsx, API URL and analytics conventions. Use for any frontend/ or map UI task.
---

# Map UI Patterns

Next.js 15 App Router + React 19 + MapLibre GL 5. TypeScript strict.
Imports use the `@/` alias → `frontend/src/` (e.g. `@/app/lib/Layerer`).

## Anatomy of a map widget (IControl)

Widgets are plain classes implementing MapLibre's `IControl`, one per file in
`src/app/components/`, PascalCase names ending in `Control`:

```tsx
import maplibregl, { IControl, Map as MapType } from "maplibre-gl";

export class ExampleControl implements IControl {
  private container: HTMLDivElement | null = null;
  private map: MapType | null = null;

  onAdd(map: MapType): HTMLElement {
    this.map = map;
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    // build DOM, attach listeners here
    return this.container;
  }

  onRemove(): void {
    this.container?.remove();
    this.container = null;
    this.map = null;
  }
}
```

Register inside `map.on("load", ...)` in `src/app/components/Map.tsx`:
`map.addControl(new ExampleControl(), "top-right");`
Study `ReportPanelControl.tsx` (panel) and `BatchProcessingControl.tsx`
(complex flow) as references.

## API base URL

Always: `const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";`
Known debt: this is duplicated per file — if touching several call sites,
prefer extracting `src/app/lib/config.ts` and importing from it.

## Layers

All vector-tile sources/layers are wired in `src/app/lib/Layerer.tsx`
(`addLayers(map)`), pointing at backend `/tiles/...` routes. Add new layers
there, following the existing source/layer id naming.

## Analytics

Track user actions with `trackEvent(eventType, endpoint, metadata)` from
`@/app/lib/analytics` — see `Map.tsx` `map_interaction` example.

## Non-obvious constraints

- Map is bounded to India (`INDIA_BOUNDS` in Map.tsx), max zoom 15
- Basemap comes from `tiles.openfreemap.org` — no key, don't change casually
- `src/middleware.ts` applies Basic Auth when `BASIC_AUTH_PASS` is set
- No test framework: verify = `npm run lint` + `npm run build`
````

- [ ] **Step 2: Verify** — `Test-Path .github/skills/map-ui/SKILL.md` → `True`.

- [ ] **Step 3: Commit**

```bash
git add .github/skills/map-ui
git commit -m "docs: Add map-ui skill"
```

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

### Task 7: frontend-dev agent

**Files:**
- Create: `.github/agents/frontend-dev.md`

**Interfaces:**
- Consumes: map-ui skill (Task 4), verify skill (Task 2).
- Produces: agent name `frontend-dev` referenced in `AGENTS.md` BUILD rule.

- [ ] **Step 1: Create `.github/agents/frontend-dev.md`** with exactly this content:

````markdown
---
name: frontend-dev
description: Implements frontend/map UI tasks for zonal-analytics (Next.js 15 + MapLibre GL 5). Delegate map controls, panels, and layer wiring here.
---

You are the frontend developer for zonal-analytics (Next.js 15, React 19,
MapLibre GL 5, TypeScript strict).

## Context to load first

- `docs/codebase/STRUCTURE.md` and `docs/codebase/CONVENTIONS.md`
- The map-ui and verify skills (`.github/skills/`)

## Ground rules

1. Follow the IControl pattern from the map-ui skill for any map widget —
   one PascalCase class per file in `src/app/components/`, registered in
   `Map.tsx` inside `map.on("load", ...)`.
2. Layer/source wiring goes in `src/app/lib/Layerer.tsx`, nowhere else.
3. API base URL: `process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000"`;
   if you touch 2+ call sites, extract `src/app/lib/config.ts` instead of
   duplicating again.
4. Use the `@/` import alias, never long relative paths.
5. Track meaningful user actions via `trackEvent` from `@/app/lib/analytics`.
6. Do not add dependencies without flagging it in your summary.
7. Before finishing: `npm run lint` and `npm run build` from `frontend/`
   must pass — paste the results.

## Output (feeds the user's learning walkthrough)

End with a **plain-language summary**: what you built, how a user reaches it
in the UI, which files changed and why — written for someone who did not
watch you work. No jargon without a one-line definition.
````

- [ ] **Step 2: Verify** — `Test-Path .github/agents/frontend-dev.md` → `True`.

- [ ] **Step 3: Commit**

```bash
git add .github/agents/frontend-dev.md
git commit -m "docs: Add frontend-dev custom agent"
```

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
