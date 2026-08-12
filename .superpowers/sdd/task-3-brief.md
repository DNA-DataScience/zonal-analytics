## Global Constraints

- Commits: single line only, `<type>: <Capitalized imperative subject>`, ≤72 chars, no issue numbers, no body, no trailers (types: feat, fix, chore, docs, test, refactor)
- `AGENTS.md` must stay under ~60 content lines
- All file contents in this plan are final — copy verbatim
- No production code changes in this plan
- Task 8 (git migration) MUST be executed inline with the user present — it is a git lesson, not a background chore

**What you'll learn (whole plan):** how agent instruction files, skills, and custom agents fit together; how to merge diverged branches and rename a branch safely.


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



