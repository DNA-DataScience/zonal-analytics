# Copilot Development Structure — Design

**Date:** 2026-07-08
**Status:** Approved
**Author:** suzman6 + Copilot CLI

## Goal

Set up a repo-level structure of Copilot instructions, skills, and custom agents so
every session on zonal-analytics builds quickly, follows a disciplined
spec → plan → implement → verify workflow, and actively teaches the maintainer
(code understanding and git) along the way. Also formalize the git branching model
ahead of a new team member joining (who may not use Copilot).

## Context

- Monorepo: FastAPI backend (`backend/app/`, Python 3.13, uv, raw SQL → Supabase
  PostGIS `"GisDB"`) + Next.js 15/MapLibre frontend (`frontend/`).
- Codebase knowledge docs already generated at `docs/codebase/` (7 files).
- User works solo today via Copilot CLI; a teammate joins in ~1-2 weeks.
- Superpowers plugin (brainstorming, writing-plans, TDD, etc.) available at user level.
- Known gaps (see `docs/codebase/CONCERNS.md`): test suite missing from working
  branch, no CI on this branch, no migrations, wildcard CORS.

## Decisions

| Question | Decision |
|----------|----------|
| Outcome | Repo-level Copilot instructions + agents + skills |
| Work mix | Feature dev (incl. new SCADA data use case) + stabilization |
| Audience | Solo now; onboarding-friendly for one teammate soon |
| Surface | Copilot CLI primary |
| Rigor | Structured: spec → plan → implement → verify enforced |
| Agents | Two: qa-engineer, frontend-dev (no parallel-workflow ambition) |
| Learning | Mandatory post-plan walkthrough sessions + git teaching |
| Git | `agenting` renamed to `dev`; feat branches off dev; dev → main promotions |

## 1) File Layout

```
zonal-analytics/
├── AGENTS.md                        # canonical repo brief + workflow gate
│                                    # (cross-tool standard: Copilot CLI, Codex,
│                                    #  Cursor, etc. — teammate-tool agnostic)
├── .github/
│   ├── copilot-instructions.md      # thin pointer to AGENTS.md (for IDE Copilot)
│   ├── agents/
│   │   ├── frontend-dev.md          # MapLibre/Next.js implementer
│   │   └── qa-engineer.md           # test writer (pytest + coverage)
│   └── skills/
│       ├── geospatial-backend/SKILL.md
│       ├── map-ui/SKILL.md
│       ├── verify/SKILL.md
│       └── walkthrough/SKILL.md
├── docs/
│   ├── codebase/                    # existing 7 knowledge docs
│   └── superpowers/
│       ├── specs/                   # design docs (from brainstorming)
│       ├── plans/                   # implementation plans (from writing-plans)
│       └── walkthroughs.md          # accumulated learning log
```

`AGENTS.md` stays under ~60 lines: stack summary, key commands, hard workflow
rules, commit message style, and pointers to `docs/codebase/` and the skills.
Deep knowledge lives in skills (loaded on demand) so the always-on context is
small. `.github/copilot-instructions.md` contains only a reference to AGENTS.md
so IDE Copilot surfaces pick it up too.

## 2) Enforced Workflow

For any non-trivial change:

```
1. SPEC        brainstorming skill → docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md
2. PLAN        writing-plans skill → docs/superpowers/plans/…
               plans written in plain language; each step sized to one sitting;
               each phase carries a "What you'll learn" note
3. BUILD       execute step by step; TDD where tests exist;
               qa-engineer may take test-writing; frontend-dev may take UI tasks
4. VERIFY      verify skill: uv run pytest, npm run lint, npm run build must pass
5. WALKTHROUGH mandatory learning review (see §3)
```

Trivial changes (typos, one-liners) may skip 1-2 but never 4.

Spec answers *what/why* (dialogue, 2-3 approaches, approved design — cheap to
change). Plan answers *how* (ordered steps, exact files, verification per step —
disposable). Readability requirement: specs and plans must avoid jargon dumps,
explain the *why* of each decision, and be readable cold in six months.

## 3) Walkthrough Skill (learning requirement)

After each completed plan, a structured review session:

1. **Tour** — file-by-file summary of changes in dependency order (data → API → UI)
2. **Deep-dive Q&A** — user picks any file/concept; explained with real code
3. **Comprehension check** — 2-3 questions posed *to the user*; gaps become
   explanations, not judgments
4. **Git recap** — the git commands used during the work and why (learning hook)
5. **Log** — short entry appended to `docs/superpowers/walkthroughs.md`

## 4) Custom Agents

**qa-engineer** — invoked for test-writing tasks. Knows: pytest + pytest-asyncio
conventions, mocking the async DB session, priority targets (start with
`backend/app/engine/feasibility_engine.py` — pure rule tables), and that a
historical test suite exists in git history to mine. Constraint: writes tests
only; never modifies production code to make tests pass — reports mismatches.

**frontend-dev** — takes UI tasks (map controls, panels). Knows: the IControl
class pattern in `frontend/src/app/components/`, layer wiring via `Layerer.tsx`,
the `@/` alias, MapLibre v5, the central-API-URL rule. Constraint: must produce
a plain-language summary of what it built, feeding the walkthrough.

Both agents read `docs/codebase/` and relevant skills; both must leave verify
passing.

## 5) Repo Skills

- **geospatial-backend** — `"GisDB"` schema map; MVT tile query template; raw
  SQL + semaphore pattern; end-to-end recipe for adding a layer
  (DB → `tiles.py` → `feasibility_engine.LAYER_CONFIG` → `Layerer.tsx`)
- **map-ui** — anatomy of an IControl; registering in `Map.tsx`; styling
  conventions; analytics event tracking via `lib/analytics.ts`
- **verify** — exact commands and definition of done; notes frontend has no
  test framework (lint + build only) until one is added
- **walkthrough** — the §3 process

## 6) Queued Work (not part of this setup)

First spec → plan cycle after setup: **restore tests + add CI** (gives
qa-engineer its first real job; `suzman6-split-ci-workflows-by-path` branch has
prior art). The SCADA ingestion use case follows, via the full workflow.

## 7) Git Workflow

```
main ──────────── protected, deploy-only (current reality preserved)
  └── dev ──────── renamed from agenting; shared integration branch
        ├── feat/<topic>   (user)
        ├── fix/<topic>    (user)
        └── feat/<topic>   (teammate — no Copilot required)
```

- All work on `feat/*` / `fix/*` off `dev`; merge into `dev` via PR
- Promote `dev → main` via PR only when deploy-ready (notebooks and experiments
  may stay on dev — the promotion PR selects what main receives)
- Commit style (enforced via AGENTS.md):
  - Single line only: `<type>: <Capitalized imperative subject>` — e.g.
    `feat: Add SCADA readings ingestion endpoint`
  - Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`
  - Subject ≤ 72 chars, no issue numbers/IDs/counts, no body, no trailers
- CI (created in the queued tests+CI plan) runs pytest, lint, and build on PRs
  so the teammate's pushes get the same gates without Copilot
- `docs/codebase/` doubles as teammate onboarding material
- Git learning: every walkthrough includes a git recap (§3.4)

## 8) Migration to the Git Model

Current state: `agenting` is the de-facto dev branch; `main` holds only what is
deployed. They have diverged (51 commits on main not on agenting, 12 the other
way at time of writing).

1. Commit the new structure (docs + config) on `agenting`
2. Merge `origin/main` into `agenting` so the dev line contains everything
   deployable; resolve conflicts together (git lesson: read
   `git log agenting..main` first)
3. Rename `agenting` → `dev` (`git branch -m agenting dev`, push `dev`, retire
   `agenting` on the remote)
4. Protect `main` on GitHub (require PR; require CI once it exists)
5. Clean up stale `suzman6-*` branches — merge what is wanted, delete the rest

## Validation of This Structure

- The structure itself is docs + config; validation = a dry run: start a fresh
  Copilot CLI session, confirm instructions load, invoke each skill, and run a
  small task through the full workflow.
- Verify gates protect against regressions in real code work.

## Out of Scope

- Writing the CI workflow, tests, or migrations (queued as first plan)
- SCADA ingestion design (its own future spec)
- Parallel multi-agent orchestration
