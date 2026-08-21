# Codebase Concerns

## Core Sections (Required)

### 1) Top Risks (Prioritized)

| Severity | Concern | Evidence | Impact | Suggested action |
|----------|---------|----------|--------|------------------|
| High | Test suite deleted/missing on current branch | scan high-churn shows `backend/tests/*`; `backend/tests` absent | No regression safety net | Restore or rewrite tests, starting with feasibility engine |
| High | No migrations; tables created at app startup | `backend/app/main.py:34-48` | Schema drift, risky deploys | Adopt Alembic |
| Med | CORS `allow_origins=["*"]` with credentials | `backend/app/main.py:58-65` | Security exposure | Restrict to known frontend origins |
| Med | No CI/CD on current branch | scan: "No CI/CD pipelines detected" (a `suzman6-split-ci-workflows-by-path` branch exists) | Quality gates unenforced | Merge/re-add workflows |
| Med | API base URL + fallback duplicated in 5+ frontend files | grep `NEXT_PUBLIC_API_URL` | Inconsistent behavior when env changes | Central `lib/config.ts` |

### 2) Technical Debt

| Debt item | Why it exists | Where | Risk if ignored | Suggested fix |
|-----------|---------------|-------|-----------------|---------------|
| ~95 lines commented-out Terra Draw code | Unfinished drawing/calibration feature | `frontend/src/app/components/Map.tsx:42-175` | Confusion, dead deps (terra-draw) | Delete or finish behind a flag |
| Empty `pages/_app.tsx` | Pages Router leftover | `frontend/src/app/pages/_app.tsx` | Confusion | Delete |
| `print()` error handling | Quick iteration | most backend routes vs `logging` in analytics | Invisible prod failures | Standardize on `logging` |
| Large binaries in git (17MB shapefile, 7.8MB HTML) | Data files committed | `backend/data/`, `backend/test_notebooks/` | Repo bloat | Git LFS or external storage |
| Notebooks as ingestion pipeline | Exploratory origin | `backend/*.ipynb` | Non-reproducible data loads | Promote to scripted processors |
| `pytest`, `notebook`, `matplotlib` in prod dependencies | No dep grouping | `backend/pyproject.toml` | Bloated deploys | Move to `[dependency-groups]` dev |

### 3) Security Concerns

| Risk | OWASP | Evidence | Current mitigation | Gap |
|------|-------|----------|--------------------|-----|
| Wildcard CORS + credentials | A05 | `backend/app/main.py:58-65` | Frontend Basic Auth | Backend itself is unauthenticated |
| Backend API fully unauthenticated | A01 | no auth dependency in any router | Obscurity only | Add auth if exposed publicly |
| Basic Auth default user `"tester"`, protection silently off when no password set | A07 | `frontend/src/middleware.ts:3-8` | Env-based password | Fail closed in production |
| Error details returned to client (`detail=str(e)`) | A05 | `tiles.py:85`, `main.py:100` | None | Generic error messages |

### 4) Performance and Scaling Concerns

| Concern | Evidence | Current symptom | Scaling risk | Suggested improvement |
|---------|----------|-----------------|-------------|-----------------------|
| On-the-fly MVT generation per request, no cache | `backend/app/api/tiles.py` | Repeated identical tile queries | DB saturation with more users | HTTP cache headers / tile cache |
| Tiny pool (5+5 overflow) w/ semaphores as backpressure | `connect_db.py:24-25` | Analytics retries indicate flakiness | Request queuing under load | Pooler (pgbouncer/Supavisor), monitor |
| Batch semaphore of 3, sync CSV build | `main.py:55`, `batch_processor.py` | Long requests block | Timeouts on big batches | Job queue or chunking if needed |

### 5) Fragile/High-Churn Areas

| Area | Why fragile | Churn signal | Safe change strategy |
|------|-------------|-------------|----------------------|
| `frontend/src/app/lib/Layerer.tsx` | Central layer wiring, 354 lines | 4 changes/90d | Change one layer at a time; verify in browser |
| `frontend/src/app/lib/FeedbackButton.tsx` | UI + API coupling | 4 changes/90d | Keep API contract stable |
| `frontend/src/app/components/BatchProcessingControl.tsx` | 637 lines, largest component | 3 changes/90d | Extract logic before extending |
| `backend/app/main.py` | Router hub + inline endpoints | 3 changes/90d | Move report/batch endpoints into routers |

### 6) `[ASK USER]` Questions

1. [ASK USER] Was the `backend/tests/` suite intentionally deleted in the app-refactor merge, or should it be restored?
2. [ASK USER] Should CI workflows (branch `suzman6-split-ci-workflows-by-path`) be merged into the current working branch (`agenting`)?
3. [ASK USER] Is the backend meant to stay unauthenticated (internal tool), or does it need auth before wider exposure?
4. [ASK USER] Is the Terra Draw / calibration feature planned, or should the commented code and deps be removed?
5. [ASK USER] Backend deployment target: the frontend has a Dockerfile but the backend doesn't — how is the backend deployed?

### 7) Evidence

- `docs/codebase/.codebase-scan.txt` (churn, CI, metrics sections)
- `backend/app/main.py`, `backend/app/db/connect_db.py`, `backend/app/api/tiles.py`
- `frontend/src/middleware.ts`, `frontend/src/app/components/Map.tsx`
