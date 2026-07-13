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
