# Testing Patterns

## Core Sections (Required)

### 1) Test Stack and Commands

- Primary test framework: pytest >=9.0.2 with pytest-asyncio and pytest-cov declared (`backend/pyproject.toml`) — **but no test files exist in the current tree**.
- Frontend: no test framework installed (`frontend/package.json` has no jest/vitest/playwright).
- Commands:

```bash
# Backend (would run, but collects nothing today)
cd backend && uv run pytest
# Frontend lint is the only quality gate
cd frontend && npm run lint
```

### 2) Test Layout

- Historical: `backend/tests/` with `conftest.py`, `pytest.ini`, and `test_*.py` files (test_api_endpoints, test_router, test_runway_processor, test_semaphore, test_performance, etc.) existed before the `app/` package refactor — visible in git high-churn output but absent from the working tree (`Test-Path backend\tests` → False).
- [ASK USER] Were the tests intentionally removed during the `suzman6-backend-app-refactor` merge, or lost?

### 3) Test Scope Matrix

| Scope | Covered? | Typical target | Notes |
|-------|----------|----------------|-------|
| Unit | No | engine/processors | pytest deps present; suite deleted |
| Integration | No | API + PostGIS | previously existed (test_api_endpoints.py) |
| E2E | No | map UI flows | never existed |

### 4) Mocking and Isolation Strategy

- [TODO] — no current tests to document. Historical `conftest.py` existed but is not in tree.

### 5) Coverage and Quality Signals

- Coverage tool: pytest-cov declared; no threshold configured.
- Current coverage: 0% (no tests).
- Known gaps: entire codebase; highest-value targets are `feasibility_engine.py` (pure rule tables — easy to unit test) and `runway_processor.py`.

### 6) Evidence

- `backend/pyproject.toml` (pytest deps)
- `docs/codebase/.codebase-scan.txt` (HIGH-CHURN FILES listing deleted backend/tests/*)
- Git branch check: `backend/tests` absent on current branch `agenting`
