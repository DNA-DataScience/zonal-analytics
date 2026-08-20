# Analytics Load Shedding Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove analytics heartbeat/event DB and network load across all environments while keeping analytics session start/end behavior unchanged.

**Architecture:** Backend heartbeat/event endpoints become no-op success handlers that never touch the database. Frontend analytics client stops scheduling heartbeat traffic and short-circuits event tracking calls. Session start/end flow remains intact so analytics can be restored later without reworking session lifecycle.

**Tech Stack:** FastAPI, SQLAlchemy async sessions, TypeScript (Next.js client runtime), pytest, ESLint.

## Global Constraints

- Keep `/analytics/session/start` and `/analytics/session/end` behavior unchanged.
- Disable `/analytics/heartbeat` and `/analytics/event` writes in all environments (no flag for this iteration).
- Do not change tile/report endpoint contracts.
- Follow existing backend route error-handling patterns and keep successful response shape stable.

---

### Task 1: Add backend no-op handling for heartbeat and event

**What you'll learn:** How analytics traffic reaches the DB layer and where to cut write load safely without breaking API callers.

**Files:**
- Modify: `backend/app/api/analytics.py`
- Test: `backend/tests/test_analytics_endpoints.py` (create if missing)

**Interfaces:**
- Consumes: Existing FastAPI analytics routes and request models.
- Produces:
  - `POST /analytics/heartbeat` returns JSON with `status: "ok"` and disabled/persisted indicators without DB writes.
  - `POST /analytics/event` returns JSON with `status: "ok"` and disabled/persisted indicators without DB writes.

- [ ] **Step 1: Write failing backend tests for disabled heartbeat/event persistence**

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_heartbeat_returns_disabled_payload(client: AsyncClient):
    res = await client.post("/analytics/heartbeat", json={
        "session_id": "11111111-1111-1111-1111-111111111111",
        "anonymous_id": "22222222-2222-2222-2222-222222222222",
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["persisted"] is False
    assert res.json()["disabled"] is True

@pytest.mark.asyncio
async def test_event_returns_disabled_payload(client: AsyncClient):
    res = await client.post("/analytics/event", json={
        "session_id": "11111111-1111-1111-1111-111111111111",
        "event_type": "map_interaction",
        "endpoint": None,
        "metadata": {"action": "map_loaded"},
    })
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
    assert res.json()["persisted"] is False
    assert res.json()["disabled"] is True
```

- [ ] **Step 2: Run targeted backend test to confirm current failure**

Run: `cd backend && uv run pytest tests/test_analytics_endpoints.py -q`
Expected: FAIL because responses currently attempt DB-backed behavior.

- [ ] **Step 3: Implement minimal backend no-op return paths**

```python
@router.post("/heartbeat")
async def heartbeat(...):
    return {"status": "ok", "persisted": False, "disabled": True}

@router.post("/event")
async def event(...):
    return {"status": "ok", "persisted": False, "disabled": True}
```

- [ ] **Step 4: Re-run targeted backend test**

Run: `cd backend && uv run pytest tests/test_analytics_endpoints.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/analytics.py backend/tests/test_analytics_endpoints.py
git commit -m "fix: Disable analytics heartbeat and event writes"
```

### Task 2: Stop frontend heartbeat timer and event POST calls

**What you'll learn:** How analytics side effects are triggered from map lifecycle code and how to preserve session lifecycle while dropping noisy traffic.

**Files:**
- Modify: `frontend/src/app/lib/analytics.ts`

**Interfaces:**
- Consumes: Existing `initAnalytics`, `trackEvent` call sites.
- Produces:
  - `startHeartbeat()` does not schedule periodic network writes.
  - `trackEvent()` exits without issuing `/analytics/event` fetch requests.
  - `startSession` and `endSession` remain unchanged.

- [ ] **Step 1: Add a focused frontend behavior check (lightweight runtime assertion or existing pattern)**

```ts
// Pseudocode target behavior:
// 1) initAnalytics(...) can still start a session.
// 2) startHeartbeat() does not create setInterval.
// 3) trackEvent(...) returns without fetch("/analytics/event").
```

- [ ] **Step 2: Run the frontend quality gate before change (baseline)**

Run: `cd frontend && npm run lint`
Expected: PASS.

- [ ] **Step 3: Implement minimal frontend load-shedding logic**

```ts
private startHeartbeat(): void {
  if (this.heartbeatInterval) {
    clearInterval(this.heartbeatInterval);
    this.heartbeatInterval = null;
  }
}

async trackEvent(...): Promise<void> {
  return;
}
```

- [ ] **Step 4: Re-run frontend gate**

Run: `cd frontend && npm run lint`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/lib/analytics.ts
git commit -m "fix: Remove analytics heartbeat and event traffic"
```

### Task 3: End-to-end verification for UAT-critical path

**What you'll learn:** How to confirm pool-pressure mitigation without changing tile/report contracts.

**Files:**
- Verify-only: no new files required

**Interfaces:**
- Consumes: Updated backend + frontend analytics behavior.
- Produces: Verified UAT-safe behavior for tile/report flows under reduced analytics load.

- [ ] **Step 1: Run targeted backend analytics and tile tests**

Run: `cd backend && uv run pytest tests/test_analytics_endpoints.py tests/test_tiles.py -q`
Expected: PASS.

- [ ] **Step 2: Run frontend lint/build gate for touched behavior**

Run: `cd frontend && npm run lint`
Expected: PASS.

- [ ] **Step 3: Manual API sanity check**

```bash
curl -X POST http://127.0.0.1:8000/analytics/heartbeat -H "Content-Type: application/json" -d "{\"session_id\":\"11111111-1111-1111-1111-111111111111\",\"anonymous_id\":\"22222222-2222-2222-2222-222222222222\"}"
curl -X POST http://127.0.0.1:8000/analytics/event -H "Content-Type: application/json" -d "{\"session_id\":\"11111111-1111-1111-1111-111111111111\",\"event_type\":\"map_interaction\"}"
```

Expected: both return `status=ok`, `persisted=false`, `disabled=true` and no DB error propagation.

- [ ] **Step 4: Commit verification-only adjustments if any**

```bash
git add -A
git commit -m "chore: Verify analytics load shedding behavior"
```
