# External Integrations

## Core Sections (Required)

### 1) Integration Inventory

| System | Type | Purpose | Auth model | Criticality | Evidence |
|--------|------|---------|------------|-------------|----------|
| Supabase Postgres (PostGIS) | DB | All geodata, analytics, feedback | user/password via `db.env` | High | `backend/app/db/connect_db.py` |
| OpenFreeMap tiles | External API | Basemap style (`tiles.openfreemap.org/styles/bright`) | None | High (map won't render without it) | `frontend/src/app/components/Map.tsx:34` |
| Stadia Maps search box | External API | Geocoding/search UI | [TODO: API key handling] | Med | `frontend/package.json`, `frontend/src/app/lib/Geocoder.tsx` |
| SharePoint doc link | Link | "Sources" documentation button | Org SSO | Low | `frontend/src/app/page.tsx:20` |

### 2) Data Stores

| Store | Role | Access layer | Key risk | Evidence |
|-------|------|--------------|----------|----------|
| Postgres schema `"GisDB"` | airport_layers, mod_layers, reserve_forests (PostGIS, geom3857) | Raw SQL via async SQLAlchemy | Schema name hardcoded in many query strings | `backend/app/api/tiles.py` |
| Analytics tables | sessions/heartbeats/events, created at startup | `app/api/analytics.py` | No migrations; created via lifespan | `backend/app/main.py:34-48` |
| Feedback table | User feedback | `app/api/feedback.py` | Same | `backend/app/api/feedback.py` |
| Local files `backend/data/` | Source-of-truth raw geodata (shapefiles, KMZ, CSV, PDF) | Notebooks ingest into DB | Large binaries in git; ingestion is manual | `backend/processor.ipynb`, `backend/MoD_processor.ipynb` |

### 3) Secrets and Credentials Handling

- Credential sources: `backend/db.env` (gitignored — verified `backend/.gitignore`), template `backend/env-Template`; frontend `BASIC_AUTH_USER/PASS` env.
- Hardcoding checks: no DB credentials in code; a commented-out localhost DB URL in `connect_db.py:20`. Frontend Basic Auth username defaults to `"tester"` in code (`middleware.ts:3`).
- Rotation/lifecycle: [TODO: unknown]

### 4) Reliability and Failure Behavior

- Retry/backoff: only analytics heartbeats (`HEARTBEAT_RETRY_DELAYS_SECONDS`, `analytics.py:18-19`); other endpoints fail fast.
- Timeouts: connection timeout 8s, command timeout 10s, pool_timeout 30s, pool_recycle 300s, pre-ping enabled (`connect_db.py:22-39`).
- Fallback: pool disposal with 30s cooldown on transient failures (`reset_db_pool_if_needed`). Tiles return empty MVT on no data; 204 above zoom 15.

### 5) Observability for Integrations

- Logging around external calls: `print()` in tile/report routes; `logging` in analytics only.
- Metrics/tracing: none.
- Gaps: no request logging middleware, no error aggregation, no health-check endpoint. [TODO]

### 6) Evidence

- `backend/app/db/connect_db.py`
- `backend/env-Template`, `backend/.gitignore`
- `backend/app/api/analytics.py`, `frontend/src/middleware.ts`
