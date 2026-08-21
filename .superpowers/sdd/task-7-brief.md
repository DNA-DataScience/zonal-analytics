## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


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



