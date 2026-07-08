# Architecture

## Core Sections (Required)

### 1) Architectural Style

- Primary style: two-tier client/server — Next.js SPA-style map client + layered FastAPI backend over PostGIS.
- Why: frontend calls backend HTTP endpoints directly (`NEXT_PUBLIC_API_URL`); backend is organized into api/db/engine/processors layers (`backend/app/`).
- Primary constraints: (1) all geospatial truth lives in Postgres/PostGIS (`"GisDB"` schema); (2) map tiles are generated on-the-fly as MVT from SQL; (3) concurrency is bounded by semaphores, not queues.

### 2) System Flow

```text
Browser (MapLibre) -> Next.js middleware (Basic Auth)
  -> map tiles:   GET /tiles/{layer}/{z}/{x}/{y}.mvt -> ST_AsMVT SQL -> PostGIS -> MVT bytes
  -> reports:     GET /report-generator?lat&lng -> report_processor -> feasibility_engine + PostGIS point-in-polygon -> JSON
  -> batch:       POST /batch-generator -> batch_processor (BATCH_SEMAPHORE=3) -> CSV StreamingResponse
  -> analytics:   POST /analytics/* -> session/heartbeat/event tables (created at startup lifespan)
  -> feedback:    POST /feedback/* -> feedback table
```

Evidence: `backend/app/main.py`, `backend/app/api/tiles.py`, `backend/app/api/analytics.py`, `frontend/src/app/lib/Layerer.tsx`.

### 3) Layer/Module Responsibilities

| Layer or module | Owns | Must not own | Evidence |
|-----------------|------|--------------|----------|
| `app/api/tiles.py` | MVT tile queries per layer (airport, mod, forest), zoom cap, TILE_SEMAPHORE(5) | Feasibility rules | `backend/app/api/tiles.py` |
| `app/engine/feasibility_engine.py` | `LAYER_CONFIG` + `FEASIBILITY_RULES` lookup tables; zone analysis | HTTP/DB session concerns | `backend/app/engine/feasibility_engine.py:18-80` |
| `app/processors/reports/` | Single-point report generation, runway funnel logic | Routing | `backend/app/processors/reports/report_processor.py` |
| `app/processors/batches/` | Multi-coordinate batch reports → CSV | Routing | `backend/app/processors/batches/batch_processor.py` |
| `app/api/analytics.py` | Session tracking with transient-DB-error retry + pool reset | Map data | `backend/app/api/analytics.py:51+` |
| `frontend Map.tsx` | Map init, control registration, India bounds | Data fetching details | `frontend/src/app/components/Map.tsx` |
| `frontend Layerer.tsx` | Adding vector-tile sources/layers pointing at backend | Map lifecycle | `frontend/src/app/lib/Layerer.tsx` |

### 4) Reused Patterns

| Pattern | Where found | Why it exists |
|---------|-------------|---------------|
| Semaphore rate-limiting | `main.py` (BATCH_SEMAPHORE=3), `tiles.py` (TILE_SEMAPHORE=5) | Protect small Supabase connection pool (pool_size=5) |
| Config-as-data rules engine | `feasibility_engine.py` LAYER_CONFIG/FEASIBILITY_RULES | Add layers without changing logic |
| MapLibre IControl classes | `frontend/src/app/components/*Control.tsx` | Encapsulate UI widgets on the map |
| Startup table creation via lifespan | `main.py` lifespan → `create_tables`, `create_feedback_table` | No migration tool in use |
| Retry + pool disposal on transient errors | `analytics.py`, `connect_db.py:reset_db_pool_if_needed` | Supabase connection flakiness |

### 5) Known Architectural Risks

- No migration system — tables created imperatively at startup; schema drift risk (`backend/app/main.py:34-48`).
- API base URL duplicated across 5+ frontend files with hardcoded fallback (`grep NEXT_PUBLIC_API_URL`).
- Raw SQL strings referencing `"GisDB"` schema scattered across routers — schema rename breaks everything.
- Large commented-out Terra Draw code in `Map.tsx` (~95 lines) suggests unfinished drawing feature.

### 6) Evidence

- `backend/app/main.py`
- `backend/app/engine/feasibility_engine.py`, `backend/app/api/tiles.py`
- `frontend/src/app/components/Map.tsx`, `frontend/src/app/lib/Layerer.tsx`
