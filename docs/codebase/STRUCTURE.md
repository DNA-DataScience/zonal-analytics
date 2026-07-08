# Codebase Structure

## Core Sections (Required)

### 1) Top-Level Map

| Path | Purpose | Evidence |
|------|---------|----------|
| `backend/` | FastAPI service (`map-back`) | `backend/pyproject.toml` |
| `backend/app/` | Application package: API, DB, engine, processors | `backend/app/main.py` |
| `backend/app/api/` | Routers: airport, tiles, points, analytics, feedback | `backend/app/api/*.py` |
| `backend/app/db/` | Async SQLAlchemy engine/session setup | `backend/app/db/connect_db.py` |
| `backend/app/engine/` | Feasibility rules engine (zone analysis) | `backend/app/engine/feasibility_engine.py` |
| `backend/app/processors/` | Report + batch report generation | `backend/app/processors/reports/`, `backend/app/processors/batches/` |
| `backend/data/` | Source geodata: shapefiles, KMZ, CSV, GeoJSON, PDF | `backend/data/` |
| `backend/*.ipynb`, `backend/test_notebooks/` | Data ingestion/exploration notebooks | `backend/processor.ipynb` |
| `frontend/` | Next.js 15 app (`map-overlay`) | `frontend/package.json` |
| `frontend/src/app/components/` | MapLibre IControl classes + Map component | `frontend/src/app/components/Map.tsx` |
| `frontend/src/app/lib/` | Non-control UI helpers, layer setup, analytics client | `frontend/src/app/lib/Layerer.tsx` |
| `docs/codebase/` | Generated codebase knowledge docs | this folder |

### 2) Entry Points

- Backend: `backend/app/main.py` — FastAPI `app` with lifespan table creation; run via `uvicorn app.main:app`.
- Frontend: `frontend/src/app/page.tsx` (renders `Map`), `frontend/src/app/layout.tsx`, plus `frontend/src/middleware.ts` (Basic Auth gate).
- Vestigial: `frontend/src/app/pages/_app.tsx` is empty (0 lines) — leftover from Pages Router. [TODO: remove?]

### 3) Module Boundaries

| Boundary | What belongs here | What must not be here |
|----------|-------------------|------------------------|
| `app/api/*` | Route handlers, request/response models, raw SQL queries | Feasibility business rules |
| `app/engine/` | Zone priority + feasibility rules (`LAYER_CONFIG`, `FEASIBILITY_RULES`) | HTTP or DB session management |
| `app/processors/` | Report/batch orchestration, CSV generation | Route definitions |
| `app/db/` | Engine, session factory, pool reset helper | Queries or business logic |
| `frontend/src/app/components/` | MapLibre `IControl` implementations | API base-url logic duplicated per file (currently violated — see CONCERNS) |
| `frontend/src/app/lib/` | Layer wiring, analytics, buttons, toast | Map instantiation |

### 4) Naming and Organization Rules

- Backend files: snake_case modules (`feasibility_engine.py`, `batch_processor.py`).
- Frontend components: PascalCase `.tsx` (`BatchProcessingControl.tsx`); utilities camelCase `.ts` (`toast.ts`, `analytics.ts`).
- Directory organization: layer-based on backend (api/db/engine/processors); rough component/lib split on frontend.
- Import alias: `@/*` → `frontend/src/*` (`frontend/tsconfig.json` paths).

### 5) Evidence

- `docs/codebase/.codebase-scan.txt` (directory tree)
- `backend/app/main.py` (router registration)
- `frontend/tsconfig.json` (alias), `frontend/src/app/components/Map.tsx`
