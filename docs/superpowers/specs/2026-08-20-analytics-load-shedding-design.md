# Analytics Load Shedding for UAT Stability

## Context

Tile requests are failing with `asyncpg.exceptions.InternalServerError: (EMAXCONNSESSION) max clients reached in session mode - max clients are limited to pool_size: 15`.

The backend uses a small async SQLAlchemy pool and all requests share the same Postgres session-mode capacity. High-frequency analytics writes (`/analytics/heartbeat` every 30s per client and `/analytics/event` on interactions) add avoidable connection pressure while UAT focuses on core feasibility and tile/report behavior.

## Goal

Protect UAT stability by eliminating heartbeat and event write load, while preserving session start/end behavior and existing tile/report APIs.

## Scope

1. **Backend**
   - Keep `/analytics/session/start` and `/analytics/session/end` unchanged.
   - Make `/analytics/heartbeat` and `/analytics/event` no-op success responses without any DB query/commit work.
2. **Frontend**
   - Keep analytics client initialization and session start/end flow intact.
   - Remove heartbeat scheduling and event POST traffic (`trackEvent`) so no heartbeat/event network calls are emitted.
3. **Non-goals**
   - No env-flag toggles for this iteration.
   - No schema changes or analytics table lifecycle changes.
   - No refactor of unrelated tile/report logic.

## Design

### Backend behavior change

- In `backend/app/api/analytics.py`:
  - `heartbeat` returns a stable payload indicating disabled persistence and does not touch DB.
  - `event` returns `{ "status": "ok", "persisted": false, "disabled": true }` and does not touch DB.
- Keep API contract success-shaped to avoid frontend failures and avoid retry storms.

### Frontend behavior change

- In `frontend/src/app/lib/analytics.ts`:
  - `startHeartbeat()` will not schedule the timer.
  - `trackEvent()` will return immediately (no fetch call).
- Session lifecycle still works (`startSession`, `endSession`) for potential future analytics restoration.

## Error handling

- No silent server exceptions are introduced because disabled paths avoid DB access entirely.
- Existing error handling remains in place for session start/end.

## Testing and verification

1. Backend tests (if available): run `uv run pytest`.
2. Frontend gate for touched TS code: run `npm run lint`.
3. Manual sanity:
   - Map loads without analytics heartbeat/event network traffic.
   - Session start/end endpoints continue returning success.
   - Tile endpoint no longer collides with heartbeat/event bursts from the same user session.

## Risks and mitigations

- **Risk:** Reduced analytics visibility during UAT.
  - **Mitigation:** Explicitly constrained as temporary load-shedding decision; session boundaries remain.
- **Risk:** Frontend expects event persistence semantics.
  - **Mitigation:** Keep response status successful and keep API shape stable.
