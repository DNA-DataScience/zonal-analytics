# Technology Stack

## Core Sections (Required)

### 1) Runtime Summary

| Area | Value | Evidence |
|------|-------|----------|
| Primary languages | Python (backend), TypeScript/React (frontend) | `backend/pyproject.toml`, `frontend/tsconfig.json` |
| Runtime + version | Python >=3.13 (backend); Node 22 (frontend, per Dockerfile) | `backend/pyproject.toml`, `frontend/Dockerfile` |
| Package managers | `uv` (backend — `uv.lock` present); `npm` (frontend — `package-lock.json`) | `backend/uv.lock`, `frontend/package-lock.json` |
| Module/build system | FastAPI app package (`app/`); Next.js 15 build (standalone output) | `backend/app/main.py`, `frontend/next.config.ts`, `frontend/Dockerfile` |

### 2) Production Frameworks and Dependencies

**Backend** (`backend/pyproject.toml`):

| Dependency | Version | Role in system | Evidence |
|------------|---------|----------------|----------|
| fastapi | >=0.118.0 | HTTP API framework | `backend/app/main.py` |
| uvicorn / gunicorn | >=0.37.0 / >=23.0.0 | ASGI server / process manager | `backend/app/main.py:102-105` |
| sqlalchemy[asyncio] + asyncpg | >=2.0.43 / >=0.31.0 | Async Postgres access | `backend/app/db/connect_db.py` |
| geoalchemy2, geopandas, shapely, fiona, pyogrio | various | Geospatial data processing | `backend/pyproject.toml` |
| mapbox-vector-tile | >=2.2.0 | MVT tile handling | `backend/app/api/tiles.py` |
| polars | >=1.33.1 | DataFrame processing | `backend/pyproject.toml` |
| camelot-py, tabula-py, lxml | various | PDF/table extraction (data ingestion) | `backend/pyproject.toml`, `backend/data/Airports_Radio.pdf` |
| folium, matplotlib, notebook | various | Notebook-based data exploration | `backend/*.ipynb` |
| dotenv | >=0.9.9 | Env loading from `db.env` | `backend/app/db/connect_db.py:10` |

**Frontend** (`frontend/package.json`):

| Dependency | Version | Role in system | Evidence |
|------------|---------|----------------|----------|
| next | 15.5.3 | React framework (App Router) | `frontend/src/app/` |
| react / react-dom | 19.1.0 | UI library | `frontend/package.json` |
| maplibre-gl | ^5.7.3 | Map rendering | `frontend/src/app/components/Map.tsx` |
| @maplibre/maplibre-gl-geocoder, @stadiamaps/maplibre-search-box | ^1.9.0 / ^3.1.0 | Geocoding/search | `frontend/src/app/lib/Geocoder.tsx` |
| terra-draw (+ @watergis/maplibre-gl-terradraw) | ^1.18.1 | Drawing tools (partially disabled — commented out in Map.tsx) | `frontend/src/app/components/Map.tsx:42-136` |

### 3) Development Toolchain

| Tool | Purpose | Evidence |
|------|---------|----------|
| pytest, pytest-asyncio, pytest-cov | Backend testing (listed as prod deps; no tests currently in tree) | `backend/pyproject.toml` |
| eslint 9 + eslint-config-next | Frontend linting | `frontend/eslint.config.mjs` |
| prettier ^3.6.2 | Formatting (note: listed under `dependencies`, not `devDependencies`) | `frontend/package.json` |
| tailwindcss 4 (+ @tailwindcss/postcss) | Styling | `frontend/postcss.config.mjs` |
| TypeScript 5, strict mode | Type checking | `frontend/tsconfig.json` |
| Jupyter notebooks | Data ingestion/exploration | `backend/processor.ipynb`, `backend/MoD_processor.ipynb` |

### 4) Key Commands

```bash
# Backend (from backend/)
uv sync                                   # install
uv run uvicorn app.main:app --reload      # run dev server
uv run pytest                             # tests [TODO: no tests in tree currently]

# Frontend (from frontend/)
npm ci            # install
npm run dev       # dev server (localhost:3000)
npm run build     # production build
npm run lint      # eslint
```

### 5) Environment and Config

- Config sources: `backend/db.env` (gitignored; template at `backend/env-Template`), Next.js env vars.
- Required backend env vars: `user`, `password`, `host`, `port`, `dbname` (`backend/app/db/connect_db.py:12-16`); optional `ENV=dev` skips dotenv load.
- Required frontend env vars: `NEXT_PUBLIC_API_URL` (defaults to `http://127.0.0.1:8000`), optional `BASIC_AUTH_USER`/`BASIC_AUTH_PASS` (`frontend/src/middleware.ts`).
- Deployment: frontend has a multi-stage Dockerfile (standalone Next output); backend has no Dockerfile. [TODO: backend deployment method]

### 6) Evidence

- `backend/pyproject.toml`, `backend/uv.lock`
- `frontend/package.json`, `frontend/tsconfig.json`, `frontend/Dockerfile`
- `backend/app/db/connect_db.py`, `backend/env-Template`
