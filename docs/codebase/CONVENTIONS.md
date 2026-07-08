# Coding Conventions

## Core Sections (Required)

### 1) Naming Rules

| Item | Rule | Example | Evidence |
|------|------|---------|----------|
| Backend files | snake_case | `feasibility_engine.py` | `backend/app/engine/` |
| Frontend components | PascalCase .tsx | `BatchProcessingControl.tsx` | `frontend/src/app/components/` |
| Frontend utils | camelCase .ts | `analytics.ts`, `toast.ts` | `frontend/src/app/lib/` |
| Python functions | snake_case | `generate_batch_report` | `backend/app/processors/batches/batch_processor.py` |
| Pydantic models | PascalCase | `BatchRequest`, `SessionStartRequest` | `backend/app/main.py:17-23` |
| Constants | UPPER_SNAKE | `BATCH_SEMAPHORE`, `LAYER_CONFIG`, `INDIA_BOUNDS` | `backend/app/main.py:55`, `Map.tsx:14` |
| Env vars (backend) | lowercase (`user`, `password`, `host`) — nonstandard | `backend/env-Template` | `backend/app/db/connect_db.py:12-16` |

### 2) Formatting and Linting

- Formatter: Prettier ^3.6.2 (no config file — defaults; IDE integration via `frontend/.idea/prettier.xml`). No Python formatter configured. [TODO]
- Linter: ESLint 9 flat config extending `next/core-web-vitals` + `next/typescript` (`frontend/eslint.config.mjs`). No Python linter (no ruff/flake8 config). [TODO]
- Run commands: `npm run lint` (frontend). Backend: none.

### 3) Import and Module Conventions

- Frontend: absolute imports via `@/app/...` alias (`frontend/tsconfig.json`); e.g. `import { addLayers } from "@/app/lib/Layerer"`.
- Backend: absolute package imports rooted at `app.` (e.g. `from app.db.connect_db import get_db`).
- No barrel files; `__init__.py` files are empty.

### 4) Error and Logging Conventions

- Backend: try/except in each route, `print()` for errors, re-raise as `HTTPException` (`tiles.py:83-85`, `main.py:98-100`). `analytics.py` is the exception — uses `logging.getLogger(__name__)` with retry logic.
- Frontend: `console.log/warn/error` throughout (`Map.tsx`).
- No structured logging or redaction rules. [TODO: adopt consistent logging strategy — see CONCERNS]

### 5) Testing Conventions

- No tests currently in tree. Git history shows a `backend/tests/` suite (pytest, `test_*.py` naming, `conftest.py`) existed pre-refactor (scan high-churn list). [ASK USER] — restore tests?
- pytest + pytest-asyncio + pytest-cov are declared dependencies (`backend/pyproject.toml`).

### 6) Evidence

- `frontend/eslint.config.mjs`, `frontend/tsconfig.json`
- `backend/app/api/tiles.py`, `backend/app/api/analytics.py`
- `docs/codebase/.codebase-scan.txt` (high-churn: deleted `backend/tests/*`)
