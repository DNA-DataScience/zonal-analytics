# Inner Zones Map Layer — Implementation Plan

> **For the next session:** follow this plan in order. It implements the approved design in [docs/superpowers/specs/2026-07-21-inner-zones-map-layer-design.md](../specs/2026-07-21-inner-zones-map-layer-design.md). The layer is **visual-only**: do not edit feasibility, report, batch, or notebook ingestion code.

**Goal:** Serve the existing `"GisDB".inner_zones` polygons as Mapbox Vector Tiles and display them by default on the MapLibre map with category-specific red shades.

**Architecture:** The FastAPI tile router reads `geom3857` from the existing PostGIS table and transforms only the current map tile into MVT bytes. The Next.js map registers one vector source pointing to that endpoint, then renders a single fill layer whose MapLibre `match` expressions select fill and outline colors from each feature’s `category` property.

**Tech stack:** FastAPI + async SQLAlchemy + PostGIS `ST_AsMVT`; Next.js 15 + React 19 + MapLibre GL 5; pytest (focused backend coverage); npm lint/build gates.

## Non-negotiable Constraints

- Start a branch named `feat/inner-zones-map-layer` from `dev`; do not work directly on `dev`.
- Preserve the user’s existing modified notebook, `backend/test_notebooks/Forest.ipynb`. Do not stage, edit, or rerun its `if_exists="replace"` upload cell.
- Treat `"GisDB".inner_zones` as an existing production data dependency. Use read-only checks only.
- Keep the feature visual-only. Do **not** add it to `LAYER_CONFIG`, `FEASIBILITY_RULES`, report processors, batch processors, or CSV outputs.
- Use raw SQL with `sqlalchemy.text`, `Depends(get_db)`, `TILE_SEMAPHORE`, and `MAX_ZOOM` from [backend/app/api/tiles.py](../../../backend/app/api/tiles.py).
- Add map sources and layers only through [frontend/src/app/lib/Layerer.tsx](../../../frontend/src/app/lib/Layerer.tsx). Do not create a new map control or alter the existing layer toggle.
- New commit messages must be one line: `<type>: <Capitalized imperative subject>`, maximum 72 characters, with no body or trailers.

---

## Phase 1 — Establish a Safe Starting Point

**What you’ll learn:** how the same PostGIS geometry is stored in EPSG:4326 for source fidelity and EPSG:3857 for fast web-tile queries.

### Task 1: Create the feature branch and protect existing work

**Files:** none.

- [ ] Confirm the working tree status and record the existing user-owned changes, especially [backend/test_notebooks/Forest.ipynb](../../../backend/test_notebooks/Forest.ipynb).
- [ ] Fetch `origin`, check out `dev`, pull the current remote branch, and create `feat/inner-zones-map-layer`.
- [ ] Confirm no notebook or unrelated IDE files are staged before any commit.

**Verify:** `git status -sb` shows the feature branch and retains unrelated existing changes unstaged.

### Task 2: Validate the already-uploaded table without modifying it

**Files:** none.

- [ ] From `backend/`, use the configured database connection to run a read-only query against `"GisDB".inner_zones`.
- [ ] Confirm all of the following before writing the endpoint:
  - the table exists;
  - `geometry` is `geometry(MultiPolygon, 4326)` and `geom3857` is `geometry(MultiPolygon, 3857)`;
  - `geom3857` has no unexpected nulls;
  - the six approved category strings occur and no unexpected category will break styling;
  - the `geom3857` GiST index and `category` index exist;
  - the geometry type is polygonal.
- [ ] If the schema differs from the design, stop and reconcile the data contract in the spec/plan before implementing. Do not change the table as part of API/UI work.

**Verify:** record the row count and grouped category counts in the implementation notes or PR description.

---

## Phase 2 — Define and Test the Tile Contract

**What you’ll learn:** how a vector-tile endpoint keeps responses small by selecting only features inside the requested Web Mercator tile envelope.

### Task 3: Add focused tests for the new route behavior

**Files:**

- Create: `backend/tests/test_tiles.py` (or extend it if it exists by the time implementation begins)

- [ ] First inspect whether `backend/tests/` has been restored since this plan was written. Follow its existing `pytest` configuration if present.
- [ ] If no test structure exists, create only the minimum test setup required for this route; do not attempt to restore the historical suite as part of this feature.
- [ ] Write the test before the route implementation using a fake async session whose `execute()` records SQL parameters and returns either MVT bytes or `None`.
- [ ] Cover these observable behaviors:
  - normal tile request passes `z`, `x`, and `y` to the database and returns the MVT media type with supplied bytes;
  - an empty result returns `b""` with the MVT media type;
  - a request above `MAX_ZOOM` returns status 204 without querying the database;
  - a database exception becomes an HTTP 500 response.
- [ ] Keep tests database-free. They must not require Supabase credentials or mutate `"GisDB".inner_zones`.

**Verify:** run `uv run pytest backend/tests/test_tiles.py` from the repository root only if project test paths support it; otherwise run `uv run pytest` from `backend/` and record the collected/passed count.

### Task 4: Add the inner-zones MVT query and endpoint

**Files:**

- Modify: [backend/app/api/tiles.py](../../../backend/app/api/tiles.py)

- [ ] Add a constant `INNER_ZONES_QUERY` beside the other MVT query constants.
- [ ] Use this query shape, with the layer name exactly `inner_zones`:
  - outer `ST_AsMVT(tile, 'inner_zones', 4096, 'geometry')`;
  - inner selected properties: `"Name"`, `category`, `state_code`, `state_name`;
  - geometry expression: `ST_AsMVTGeom(geom3857, ST_TileEnvelope(:z, :x, :y), 4096, 256, true) AS geometry`;
  - source table: `"GisDB".inner_zones`;
  - envelope filter: `geom3857 && ST_TileEnvelope(:z, :x, :y)`.
- [ ] Add `get_inner_zones_tile()` at `GET /inner-zones/{z}/{x}/{y}.mvt`.
- [ ] Match the existing endpoint contract exactly: return 204 above `MAX_ZOOM`, use `async with TILE_SEMAPHORE`, return `application/vnd.mapbox-vector-tile`, return empty bytes for a tile with no features, and translate route errors to HTTP 500.
- [ ] Prefer `logging` for the new endpoint’s exception message if it can be added without refactoring the existing routes; do not perform unrelated cleanup of the other handlers.
- [ ] Do not change [backend/app/main.py](../../../backend/app/main.py): it already mounts the tile router at `/tiles`.

**Verify:** rerun the focused route test from Task 3; confirm the expected route path is `/tiles/inner-zones/{z}/{x}/{y}.mvt` because `main.py` supplies the `/tiles` prefix.

### Task 5: Smoke-test the live tile with the uploaded data

**Files:** none.

- [ ] Start the backend locally using its normal `uvicorn app.main:app --reload` command with the configured database environment.
- [ ] Request a tile at a known populated zoom/x/y location. If no known location is available, calculate one from a read-only bounding-box query; do not guess repeatedly against production.
- [ ] Confirm HTTP 200, MVT content type, and a non-empty binary body for a populated tile.
- [ ] Confirm an empty viewport returns a valid empty tile and a zoom above 15 returns 204.

**Verify:** retain the status/content-type/body-size evidence. Stop the local server when the smoke test is complete.

---

## Phase 3 — Render Inner Zones on the Map

**What you’ll learn:** how MapLibre uses a vector source for transport and a style expression to choose each polygon’s appearance from feature properties.

### Task 6: Add one vector source and one category-driven layer

**Files:**

- Modify: [frontend/src/app/lib/Layerer.tsx](../../../frontend/src/app/lib/Layerer.tsx)

- [ ] Follow the existing airport, forest, and MoD source pattern inside `addLayers(map)`.
- [ ] Register `inner-zones-tiles` if it is not already present:
  - type `vector`;
  - tiles: `${apiBaseUrl}/tiles/inner-zones/{z}/{x}/{y}.mvt`;
  - `minzoom: 0`, `maxzoom: 15`.
- [ ] Add exactly one default-visible fill layer with ID `inner-zones`, source `inner-zones-tiles`, and `source-layer: "inner_zones"`.
- [ ] Insert it through `addBelowLabels` so place labels remain readable.
- [ ] Set initial `fill-opacity` to `0.32`.
- [ ] Use MapLibre `match` expressions on `['get', 'category']` with these approved colors:

  | Category                   | Fill      | Outline   |
  | -------------------------- | --------- | --------- |
  | Animal/Bird Migratory Path | `#fee2e2` | `#fca5a5` |
  | Coastal Regulatory Zone    | `#fecaca` | `#fb7185` |
  | Heritage                   | `#fda4af` | `#f43f5e` |
  | Reservoir                  | `#fb7185` | `#e11d48` |
  | Sanctuary                  | `#f87171` | `#dc2626` |
  | Defence Protected Area     | `#ef4444` | `#991b1b` |

- [ ] Provide neutral fallback fill/outline values for an unexpected category.
- [ ] Do not add `LayerToggleControl`, a new control, an analytics event, a popup, or a legend in this plan. The layer must be visible when the map opens.
- [ ] Do not add dependencies.

**Verify:** TypeScript accepts the source/layer definitions and the existing layers still register only once after map style reloads.

### Task 7: Perform browser-level map validation

**Files:** none.

- [ ] Start the backend and frontend locally with `NEXT_PUBLIC_API_URL` pointed at the local backend.
- [ ] Open the map and confirm `/tiles/inner-zones/...` requests succeed.
- [ ] Check that each available category appears in a distinguishable red shade, labels remain above fills, and opacity allows the basemap to remain visible.
- [ ] Pan and zoom across at least two populated regions, then toggle the basemap/style if that flow is available to confirm the source/layer is restored without duplicate-layer errors.
- [ ] Confirm airport, forest, MoD, CMS, and WTG behavior remains unaffected.

**Verify:** capture the browser findings in the PR/implementation notes, including any category that is not present in the current uploaded data.

---

## Phase 4 — Full Verification and Delivery

**What you’ll learn:** how lint, production builds, direct API checks, and a review of the final diff catch different kinds of regressions.

### Task 8: Run required gates and review scope

**Files:** all changed files.

- [ ] Run backend verification from `backend/`:
  - `uv run pytest`
  - `uv run python -c "import app.main"`
- [ ] Run frontend verification from `frontend/`:
  - `npm run lint`
  - `npm run build`
- [ ] If any gate fails, read the complete output, fix only the relevant failure, and rerun that same gate before proceeding.
- [ ] Review `git diff --check` and `git diff -- backend/app/api/tiles.py frontend/src/app/lib/Layerer.tsx backend/tests`.
- [ ] Confirm no modifications exist under `backend/test_notebooks/`, feasibility engine, report/batch processors, or database schema files.
- [ ] If `pytest` still reports no tests except the new focused test, state that plainly; do not claim broad backend coverage.

**Verify:** record actual command outputs and browser/API smoke-test evidence before declaring the feature complete.

### Task 9: Commit, request review, and run the mandatory walkthrough

**Files:** all completed implementation files; later append to `docs/superpowers/walkthroughs.md` during walkthrough.

- [ ] Commit the implementation after all applicable gates pass, for example: `feat: Add inner zones map layer`.
- [ ] Open a PR from `feat/inner-zones-map-layer` into `dev`, summarizing the visual-only scope, endpoint, tile layer name, validation evidence, and the fact that the notebook/database upload was intentionally untouched.
- [ ] Request code review before merge, following the repository workflow.
- [ ] Run the mandatory user walkthrough in data → API → UI order:
  1. explain the verified database contract;
  2. explain MVT generation in `tiles.py`;
  3. explain the MapLibre source and category `match` style in `Layerer.tsx`;
  4. ask 2–3 comprehension-check questions;
  5. recap git commands actually used;
  6. append a concise entry to `docs/superpowers/walkthroughs.md` and commit it separately as `docs: Log walkthrough for inner zones`.

**Verify:** the PR is review-ready, all gates are documented, and the walkthrough log entry matches the work that was actually completed.

## Expected Changed Files

| File                               | Purpose                                                                                |
| ---------------------------------- | -------------------------------------------------------------------------------------- |
| `backend/app/api/tiles.py`         | MVT SQL constant and `/inner-zones/...` tile handler.                                  |
| `backend/tests/test_tiles.py`      | Focused, database-free coverage for the tile route, if no equivalent test file exists. |
| `frontend/src/app/lib/Layerer.tsx` | `inner-zones-tiles` vector source and the default-visible category-colored fill layer. |
| `docs/superpowers/walkthroughs.md` | Added only after the mandatory completion walkthrough.                                 |

No change is expected in `backend/app/main.py`, `backend/app/engine/`, report/batch processors, the upload notebook, or the PostGIS schema.
