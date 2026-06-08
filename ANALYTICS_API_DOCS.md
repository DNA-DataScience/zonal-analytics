# Analytics API — Frontend Integration Guide

This document describes the analytics tracking API. The frontend must implement session lifecycle management and event tracking by calling these endpoints.

---

## Base URL

| Environment | URL |
|---|---|
| Development | `http://localhost:8000` |
| Production | `https://<your-api-domain>` |

All endpoints are prefixed with `/analytics`.  
All requests and responses use `Content-Type: application/json`.

---

## Anonymous ID

- Generate a **UUID v4** on the user's first visit.
- Persist it in `localStorage` under the key `analytics_anonymous_id`.
- Reuse the same ID on every subsequent visit — this is how returning visitors are identified.
- Never regenerate it unless the user clears their browser storage.

---

## Session ID

- Obtained from the `POST /analytics/session/start` response.
- Store in `sessionStorage` under the key `analytics_session_id`.
- Scoped to a single tab/session — not shared across tabs, not persisted across page reloads.

---

## Endpoints

### 1. Start Session

**`POST /analytics/session/start`**

Call **once on app load** (e.g., in your root component or app entry point).

**Request Body:**
```json
{
  "anonymous_id": "550e8400-e29b-41d4-a716-446655440000",
  "client_env": "production",
  "user_agent": "Mozilla/5.0 ...",
  "referrer": "https://example.com"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `anonymous_id` | `string (UUID)` | Yes | Persistent anonymous ID from `localStorage` |
| `client_env` | `string` | No | `"development"` or `"production"` |
| `user_agent` | `string` | No | `navigator.userAgent` |
| `referrer` | `string \| null` | No | `document.referrer` or `null` |

**Response:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

Store `session_id` — it is required for all subsequent calls.

---

### 2. Heartbeat

**`POST /analytics/heartbeat`**

Call **every 30 seconds** while the app is open. Used by the backend to compute session duration.

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "anonymous_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{ "status": "ok" }
```

---

### 3. End Session

**`POST /analytics/session/end`**

Call **on page unload**. Use `navigator.sendBeacon` for reliable delivery, with `fetch` + `keepalive: true` as a fallback.

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "anonymous_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "status": "ok",
  "duration_seconds": 142
}
```

**Recommended implementation:**
```js
window.addEventListener('beforeunload', () => {
  const data = JSON.stringify({ session_id, anonymous_id });

  if (navigator.sendBeacon) {
    navigator.sendBeacon(`${BASE_URL}/analytics/session/end`, data);
  } else {
    fetch(`${BASE_URL}/analytics/session/end`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: data,
      keepalive: true,
    });
  }
});
```

---

### 4. Track Event

**`POST /analytics/event`**

Call whenever a meaningful user action occurs (e.g., a report is generated, an API call is made, a batch is submitted).

**Request Body:**
```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "event_type": "api_call",
  "endpoint": "/report-generator",
  "metadata": {
    "lat": 28.5,
    "lng": 77.5
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `session_id` | `string (UUID)` | Yes | Session ID from `session/start` |
| `event_type` | `string` | Yes | Short label for the action (see suggested values below) |
| `endpoint` | `string \| null` | No | Backend endpoint that was called |
| `metadata` | `object \| null` | No | Any additional context as a JSON object |

**Response:**
```json
{ "status": "ok" }
```

**Suggested `event_type` values** (agree on these with the backend team):

| Value | When to use |
|---|---|
| `api_call` | Any backend API call |
| `report_generated` | Report generation triggered |
| `batch_submitted` | Batch job submitted |
| `map_interaction` | Significant map interaction |

---

## Dev Traffic Filtering

The backend automatically marks sessions as dev traffic based on:
1. The server running with `ENV=dev`
2. The request coming from `localhost` / `127.0.0.1`
3. The request including the header `X-Client-Env: development`

**Frontend requirement:** When running in a development environment, include this header on all analytics requests:
```
X-Client-Env: development
```

This allows the backend to separate dev sessions from real user data in reports.

---

## Implementation Checklist

- [ ] Generate and persist `anonymous_id` UUID in `localStorage`
- [ ] Call `POST /analytics/session/start` on app load; store `session_id` in `sessionStorage`
- [ ] Set up `setInterval` every **30 seconds** to call `POST /analytics/heartbeat`
- [ ] Call `POST /analytics/session/end` on `beforeunload` via `sendBeacon`
- [ ] Call `POST /analytics/event` for each meaningful user action
- [ ] Send `X-Client-Env: development` header in dev environments

---

## Reference Implementation

A fully working JavaScript reference implementation is available in [`analytics.js`](./analytics.js) in this repository. The frontend agent can use it directly or port the logic to the relevant framework.
