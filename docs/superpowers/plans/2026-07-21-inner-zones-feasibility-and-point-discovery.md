# Inner Zones Feasibility and Point Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all six Inner Zones categories visible and enforce them as
hard feasibility restrictions, while making WTG/CMS points always visible and
inspectable on hover.

**Architecture:** The backend adds Inner Zones point-in-polygon reads to the
existing regular and batch report processors, then passes them through the
centralized feasibility engine. The frontend uses the existing vector tile and
GeoJSON sources, adds an accessible hover tooltip module, and uses
always-visible point layers rather than clusters.

**Tech Stack:** FastAPI, async SQLAlchemy/PostGIS, pytest, Next.js 15,
TypeScript, React 19, MapLibre GL 5, ESLint.

## Global Constraints

- Work only on `feat/inner-zones-map-layer`, based on `dev`.
- Preserve the user-owned `backend/test_notebooks/Forest.ipynb`; do not edit,
  stage, or rerun its upload cell.
- `"GisDB".inner_zones`, `"GisDB".cms_stations`, and `"GisDB".wtg_sites` are
  existing production data dependencies; use read-only queries only.
- Every Inner Zones intersection returns combined feasibility `("No", "red")`.
- Do not change airport, MoD, or forest feasibility behavior when a point has
  no Inner Zones match.
- Keep raw SQL in `sqlalchemy.text` and use the existing async session
  patterns. Do not add ORM models, migrations, or dependencies.
- Keep the tile route guarded by `TILE_SEMAPHORE` and capped by `MAX_ZOOM`.
- Retain exactly one Inner Zones MVT source and one `inner-zones` fill layer.
- Set Inner Zones fill opacity to `0.50` and use the colors in Task 5.
- Render all 9,320 WTG sites and 145 CMS stations as individual points at
  every zoom. Do not cluster or aggregate them.
- Display CMS `State / Site Office`; display WTG customer name, main site,
  readable local commission date with no time, and installed capacity on hover.
- Right-click remains the only report trigger and must work over points and
  empty map space.
- Build tooltip DOM through text nodes, never interpolated database values.
- New commit messages are one line only:
  `<type>: <Capitalized imperative subject>`, at most 72 characters, without
  a body or trailers.

---

## Phase 1 — Establish the Tile and Test Foundation

**What you'll learn:** how a database-free async test protects the public MVT
contract while PostGIS performs the actual geometry work at runtime.

### Task 1: Track focused backend tests and complete the Inner Zones tile route

**Files:**
- Modify: `backend/.gitignore`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_tiles.py`
- Modify: `backend/app/api/tiles.py`

**Interfaces:**
- Produces `INNER_ZONES_QUERY` and
  `get_inner_zones_tile(z: int, x: int, y: int, db: AsyncSession)`.
- The public endpoint is
  `GET /tiles/inner-zones/{z}/{x}/{y}.mvt`.
- Later map work consumes MVT layer name `inner_zones`.

- [ ] **Step 1: Stop ignoring the backend test directory**

Remove the `tests/` line from `backend/.gitignore`. Keep entries for test
notebook extracts and other generated artifacts unchanged.

- [ ] **Step 2: Add the minimal pytest import setup**

Create `backend/tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
```

- [ ] **Step 3: Write the failing endpoint tests**

Create `backend/tests/test_tiles.py` with a fake async session that records
the query parameters and returns a `scalar()` value. Cover these behaviors:

```python
@pytest.mark.asyncio
async def test_inner_zones_tile_returns_mvt_bytes():
    db = FakeSession(value=b"tile-bytes")
    response = await tiles.get_inner_zones_tile(8, 120, 90, db)
    assert response.status_code == 200
    assert response.media_type == "application/vnd.mapbox-vector-tile"
    assert response.body == b"tile-bytes"
    assert db.calls[0]["params"] == {"z": 8, "x": 120, "y": 90}

@pytest.mark.asyncio
async def test_inner_zones_tile_returns_empty_mvt_when_query_is_empty():
    response = await tiles.get_inner_zones_tile(8, 120, 90, FakeSession())
    assert response.status_code == 200
    assert response.body == b""

@pytest.mark.asyncio
async def test_inner_zones_tile_skips_database_above_max_zoom():
    db = FakeSession(value=b"unused")
    response = await tiles.get_inner_zones_tile(tiles.MAX_ZOOM + 1, 120, 90, db)
    assert response.status_code == 204
    assert db.calls == []

@pytest.mark.asyncio
async def test_inner_zones_tile_translates_database_error_to_500():
    with pytest.raises(HTTPException, match="db failed") as exc:
        await tiles.get_inner_zones_tile(8, 120, 90, FakeSession(error=RuntimeError("db failed")))
    assert exc.value.status_code == 500
```

- [ ] **Step 4: Verify the existing implementation against the tests**

Run from `backend/`:

```powershell
uv run pytest tests/test_tiles.py -q
```

Expected: all four tests pass. The current feature workspace already contains
the TDD-created route implementation; retain it rather than recreating it.

- [ ] **Step 5: Compare the existing MVT SQL and handler with this contract**

In `backend/app/api/tiles.py`, confirm `logging`, a module logger, and this
query beside the existing tile query constants:

```python
INNER_ZONES_QUERY = text("""
SELECT ST_AsMVT(tile, 'inner_zones', 4096, 'geometry') AS mvt
FROM (
  SELECT
    "Name",
    category,
    state_code,
    state_name,
    ST_AsMVTGeom(
      geom3857, ST_TileEnvelope(:z, :x, :y), 4096, 256, true
    ) AS geometry
  FROM "GisDB".inner_zones
  WHERE geom3857 && ST_TileEnvelope(:z, :x, :y)
) AS tile;
""")
```

Add the route:

```python
@router.get("/inner-zones/{z}/{x}/{y}.mvt")
async def get_inner_zones_tile(
    z: int, x: int, y: int, db: AsyncSession = Depends(get_db)
):
    if z > MAX_ZOOM:
        return Response(status_code=204)
    async with TILE_SEMAPHORE:
        try:
            result = await db.execute(INNER_ZONES_QUERY, {"z": z, "x": x, "y": y})
            return Response(
                content=result.scalar() or b"",
                media_type="application/vnd.mapbox-vector-tile",
            )
        except Exception as exc:
            logger.exception("Inner Zones tile error z=%s, x=%s, y=%s", z, x, y)
            raise HTTPException(status_code=500, detail=str(exc))
```

- [ ] **Step 6: Run focused tests and a live smoke test**

Run:

```powershell
uv run pytest tests/test_tiles.py -q
uv run uvicorn app.main:app --reload
```

In a separate terminal, request:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/tiles/inner-zones/8/179/114.mvt
Invoke-WebRequest http://127.0.0.1:8000/tiles/inner-zones/8/0/0.mvt
Invoke-WebRequest http://127.0.0.1:8000/tiles/inner-zones/16/179/114.mvt -SkipHttpErrorCheck
```

Expected: populated tile is `200` with MVT content and non-zero bytes; empty
tile is `200` with zero bytes; zoom 16 is `204`.

- [ ] **Step 7: Commit the endpoint foundation**

```powershell
git add backend/.gitignore backend/tests backend/app/api/tiles.py
git commit -m "feat: Add inner zones tile endpoint"
```

---

## Phase 2 — Make Inner Zones a Feasibility Restriction

**What you'll learn:** how a centralized rule engine can accept a new
restriction without altering unrelated airport, MoD, and forest decisions.

### Task 2: Extend the engine with a hard Inner Zones restriction

**Files:**
- Modify: `backend/app/engine/feasibility_engine.py`
- Create: `backend/tests/test_feasibility_engine.py`

**Interfaces:**
- Produces `find_most_restrictive_inner_zone(zones)`.
- Extends `determine_feasibility(airport_zone_type, mod_zone_type,
  forest_zone_type=None, inner_zone_type=None)`.
- Extends `build_combined_analysis(..., inner_zone_reports=None,
  most_restrictive_inner_zone=None)`.
- Produces report dictionaries with `layer: "inner_zones"`.

- [ ] **Step 1: Write failing pure-engine tests**

Create tests for each boundary of the new contract:

```python
def test_inner_zone_is_more_restrictive_than_other_layers():
    result = determine_feasibility("outer", "NO_NOC", None, "Reservoir")
    assert result == ("No", "red")

def test_no_inner_zone_preserves_existing_feasibility_rules():
    result = determine_feasibility("outer", "NO_NOC", None, None)
    assert result == ("Yes", "green")

def test_inner_zone_report_names_category_and_feature():
    report = build_inner_zone_report(
        {"category": "Reservoir", "name": "Nagarjuna Sagar"}
    )
    assert report["layer"] == "inner_zones"
    assert report["zone"] == "Reservoir"
    assert report["feasibility"] == "No"

def test_combined_analysis_counts_and_names_inner_zone_restriction():
    combined = build_combined_analysis(
        [], [], None, None, 0, [], None,
        [build_inner_zone_report({"category": "Sanctuary", "name": "Example"})],
        ("Sanctuary", {"category": "Sanctuary", "name": "Example"}),
    )
    assert combined["total_inner_zone_zones"] == 1
    assert "Inner Zones: Sanctuary - Example" in combined["contributing_restrictions"]
```

- [ ] **Step 2: Verify the tests fail**

```powershell
uv run pytest tests/test_feasibility_engine.py -q
```

Expected: import or signature failures for the Inner Zones helpers.

- [ ] **Step 3: Add the Inner Zones configuration and helper**

Add this config entry:

```python
"inner_zones": {
    "name": "Inner Zones",
    "priority_order": [
        "Animal/Bird Migratory Path",
        "Coastal Regulatory Zone",
        "Heritage",
        "Reservoir",
        "Sanctuary",
        "Defence Protected Area",
    ],
    "db_table": "inner_zones",
    "query_fields": ["name", "category", "state_code", "state_name"],
    "special_handlers": None,
},
```

Add:

```python
def find_most_restrictive_inner_zone(
    zones: List[Dict],
) -> Tuple[Optional[str], Optional[Dict]]:
    return find_most_restrictive_zone(zones, "inner_zones")
```

- [ ] **Step 4: Enforce and explain the restriction**

Extend `determine_feasibility` with `inner_zone_type`. Its first decision
must be:

```python
if inner_zone_type:
    return ("No", "red")
```

Create `build_inner_zone_report(zone_dict)` returning:

```python
{
    "layer": "inner_zones",
    "zone": zone_dict["category"],
    "name": zone_dict.get("name") or "Unknown Inner Zone",
    "type": "inner_zone",
    "min_height": "Restricted",
    "note": "No WTGs allowed in Inner Zones restricted area.",
    "feasibility": "No",
}
```

Extend `generate_combined_note` and `build_combined_analysis` to accept the
new most-restrictive item, add
`Inner Zones: <category> - <name>` to contributing restrictions, include
`total_inner_zone_zones`, and include Inner Zones reports in the minimum
height aggregation.

- [ ] **Step 5: Run the engine tests**

```powershell
uv run pytest tests/test_feasibility_engine.py -q
```

Expected: all tests pass.

- [ ] **Step 6: Commit the engine behavior**

```powershell
git add backend/app/engine/feasibility_engine.py backend/tests/test_feasibility_engine.py
git commit -m "feat: Enforce inner zones feasibility"
```

---

## Phase 3 — Include the Restriction in Both Report Pipelines

**What you'll learn:** how the same PostGIS intersection contract can serve
one interactive coordinate and an efficient batch of coordinates.

### Task 3: Add Inner Zones to regular reports and report rendering

**Files:**
- Modify: `backend/app/processors/reports/report_processor.py`
- Modify: `frontend/src/app/lib/FindZones.tsx`
- Modify: `frontend/src/app/components/ReportPanelControl.tsx`
- Create: `backend/tests/test_report_processor.py`

**Interfaces:**
- Produces `INNER_ZONES_REPORT_QUERY`.
- `generate_report()` returns combined, airport, MoD, forest, and
  `inner_zones` items.
- Frontend `ReportZone` includes `InnerZone`.

- [ ] **Step 1: Write a failing report-processor test**

Use a fake async session that returns empty airport/MoD/forest result sets and
one Inner Zones row:

```python
async def test_report_includes_inner_zone_and_returns_not_feasible():
    response = await generate_report(20.0, 73.0, db=FakeSession(
        results=[[], [], [], [("Reservoir", "Nagarjuna Sagar", "TS", "Telangana")]]
    ))
    report = json.loads(response.body)
    assert report[0]["layer"] == "combined"
    assert report[0]["feasibility"] == "No"
    assert report[0]["total_inner_zone_zones"] == 1
    assert report[-1]["layer"] == "inner_zones"
    assert report[-1]["zone"] == "Reservoir"
```

- [ ] **Step 2: Verify the test fails**

```powershell
uv run pytest tests/test_report_processor.py -q
```

Expected: the fake session is not queried for Inner Zones and no Inner Zones
report item exists.

- [ ] **Step 3: Add the read-only point intersection**

Add `INNER_ZONES_REPORT_QUERY` using the same `p` CTE as the forest query:

```sql
SELECT z.category, z."Name", z.state_code, z.state_name
FROM "GisDB".inner_zones z
JOIN p
  ON z.geom3857 && p.geom3857
 AND ST_Intersects(z.geom3857, p.geom3857);
```

Execute it after the forest query. Convert rows into:

```python
{
    "zone": row[0],
    "category": row[0],
    "name": row[1] or "Unknown Inner Zone",
    "state_code": row[2],
    "state_name": row[3],
}
```

Build individual reports, include them in the no-result and combined-analysis
conditions, pass the most restrictive result to the engine, and append the
individual Inner Zones reports to the JSON response.

- [ ] **Step 4: Extend report presentation types and HTML**

In `FindZones.tsx`, add:

```typescript
export type InnerZone = {
  layer: "inner_zones";
  zone: string;
  name: string;
  type: "inner_zone";
  feasibility: "No";
  min_height: "Restricted";
  note: string;
};
```

Add it to `ReportZone`, add `total_inner_zone_zones?: number` to
`CombinedZone`, and extend the count renderer with an Inner Zones badge.
Create `renderInnerZoneCard()` showing the name, category, and Not Feasible
badge. Add an `Inner Zones` collapsible report section following the existing
forest section. Add matching `.inner-zones-card` and `.count-inner-zones`
styles to `ReportPanelControl.tsx`.

- [ ] **Step 5: Run the focused test**

```powershell
uv run pytest tests/test_report_processor.py -q
```

Expected: the Inner Zones intersection is included and forces `No`.

- [ ] **Step 6: Commit the regular report integration**

```powershell
git add backend/app/processors/reports/report_processor.py frontend/src/app/lib/FindZones.tsx frontend/src/app/components/ReportPanelControl.tsx backend/tests/test_report_processor.py
git commit -m "feat: Add inner zones to reports"
```

### Task 4: Add Inner Zones to batch feasibility and CSV output

**Files:**
- Modify: `backend/app/processors/batches/batch_processor.py`
- Create: `backend/tests/test_batch_processor.py`

**Interfaces:**
- Produces
  `get_batch_inner_zones(coordinates: List[Dict], db: AsyncSession) -> List[Dict[str, Any]]`.
- Batch results add `most_restrictive_inner_zone`.
- CSV header adds `Most Restrictive Inner Zone`.

- [ ] **Step 1: Write failing batch tests**

Test both the query/result and final CSV:

```python
def test_batch_csv_includes_inner_zone_column():
    csv_content, _ = save_batch_to_csv(
        [{"id": 1, "lat": 20, "lon": 73}],
        [{
            "pid": 1,
            "feasibility": "No",
            "most_restrictive_airport": "No zones exist",
            "most_restrictive_mod": "No zones exist",
            "most_restrictive_forest": "No zones exist",
            "most_restrictive_inner_zone": "Reservoir - Nagarjuna Sagar",
        }],
    )
    assert "Most Restrictive Inner Zone" in csv_content.splitlines()[0]
    assert "Reservoir - Nagarjuna Sagar" in csv_content

@pytest.mark.asyncio
async def test_batch_inner_zone_forces_no_feasibility():
    result = await generate_batch_report(
        [{"id": 1, "lat": 20, "lon": 73}], FakeSession.with_inner_zone()
    )
    assert "No" in result["csv_content"]
    assert "Reservoir - Nagarjuna Sagar" in result["csv_content"]
```

- [ ] **Step 2: Verify the tests fail**

```powershell
uv run pytest tests/test_batch_processor.py -q
```

Expected: the CSV header and generated data do not include Inner Zones.

- [ ] **Step 3: Implement the batched intersection**

Copy the existing JSON `points` CTE structure. Query:

```sql
SELECT p.pid, z.category, z."Name", z.state_code, z.state_name
FROM points p
JOIN "GisDB".inner_zones z
  ON z.geom3857 && p.geom
 AND ST_Intersects(z.geom3857, p.geom)
```

Return each row as:

```python
{
    "pid": row[0],
    "zone": row[1],
    "category": row[1],
    "name": row[2] or "Unknown Inner Zone",
    "state_code": row[3],
    "state_name": row[4],
}
```

Group by `pid`, find each coordinate's most restrictive Inner Zone, pass it
to `determine_feasibility`, and call
`format_zone_description(inner_zone_type, inner_zone_dict, "inner_zones")`.

- [ ] **Step 4: Add the CSV column**

Append this header after `Most Restrictive Forest Zone`:

```python
"Most Restrictive Inner Zone"
```

Append `result.get("most_restrictive_inner_zone", "No zones exist")` to each
row in the same position.

- [ ] **Step 5: Verify the batch tests**

```powershell
uv run pytest tests/test_batch_processor.py -q
```

Expected: both tests pass, including the `No` result and CSV column.

- [ ] **Step 6: Commit batch integration**

```powershell
git add backend/app/processors/batches/batch_processor.py backend/tests/test_batch_processor.py
git commit -m "feat: Add inner zones to batch reports"
```

---

## Phase 4 — Improve Map Visibility and Discovery

**What you'll learn:** how MapLibre separates source data, visual layers, and
pointer interaction so data-heavy maps remain understandable.

### Task 5: Make all polygons and points visible at every zoom

**Files:**
- Modify: `frontend/src/app/lib/Layerer.tsx`

**Interfaces:**
- Keeps source IDs `inner-zones-tiles`, `cms-tiles`, and `wtg-tiles`.
- Keeps layer IDs `inner-zones`, `cms-stations`, and `wtg-sites`.
- Removes obsolete cluster layer IDs entirely.

- [ ] **Step 1: Set the approved Inner Zones visual contract**

Move the `inner-zones` source/layer block after the MoD polygon block, still
inserted with `addBelowLabels`. Replace its expressions with:

```typescript
"fill-color": [
  "match", ["get", "category"],
  "Animal/Bird Migratory Path", "#fecaca",
  "Coastal Regulatory Zone", "#fb7185",
  "Heritage", "#f43f5e",
  "Reservoir", "#e11d48",
  "Sanctuary", "#dc2626",
  "Defence Protected Area", "#991b1b",
  "#f3f4f6",
],
"fill-opacity": 0.50,
"fill-outline-color": [
  "match", ["get", "category"],
  "Animal/Bird Migratory Path", "#fb7185",
  "Coastal Regulatory Zone", "#e11d48",
  "Heritage", "#be123c",
  "Reservoir", "#be123c",
  "Sanctuary", "#991b1b",
  "Defence Protected Area", "#7f1d1d",
  "#9ca3af",
],
```

Leave `minzoom: 0`, `maxzoom: 15`, source layer `inner_zones`, and the
`map.getLayer("inner-zones")` guard intact.

- [ ] **Step 2: Remove CMS clustering**

Delete `cluster`, `clusterMaxZoom`, and `clusterRadius` from `cms-tiles`.
Delete `cms-clusters` and `cms-cluster-count`. Retain only one
`cms-stations` circle layer, without a cluster filter:

```typescript
paint: {
  "circle-radius": 4,
  "circle-color": "#d946ef",
  "circle-opacity": 0.88,
  "circle-stroke-width": 1,
  "circle-stroke-color": "#a61e8e",
  "circle-stroke-opacity": 1,
},
```

- [ ] **Step 3: Remove WTG clustering**

Apply the same source change to `wtg-tiles`. Delete `wtg-clusters` and
`wtg-cluster-count`. Retain only one unfiltered `wtg-sites` circle layer:

```typescript
paint: {
  "circle-radius": 2.5,
  "circle-color": "#06b6d4",
  "circle-opacity": 0.80,
  "circle-stroke-width": 0.5,
  "circle-stroke-color": "#0369a1",
  "circle-stroke-opacity": 1,
},
```

- [ ] **Step 4: Validate the static TypeScript contract**

Run from `frontend/`:

```powershell
npm run lint
npm run build
```

Expected: both commands succeed. Do not add a frontend test framework.

- [ ] **Step 5: Commit visual visibility changes**

```powershell
git add frontend/src/app/lib/Layerer.tsx
git commit -m "feat: Improve map layer visibility"
```

### Task 6: Add safe hover tooltips for CMS and WTG points

**Files:**
- Create: `frontend/src/app/lib/PointHoverTooltip.ts`
- Modify: `frontend/src/app/components/Map.tsx`

**Interfaces:**
- Produces
  `attachPointHoverTooltip(map: maplibregl.Map): () => void`.
- Consumes rendered layers `cms-stations` and `wtg-sites`.
- `Map.tsx` invokes its returned cleanup function during map teardown.

- [ ] **Step 1: Implement date and DOM helpers**

Create `PointHoverTooltip.ts` with:

```typescript
function displayValue(value: unknown): string {
  return value === null || value === undefined || value === ""
    ? "Not available"
    : String(value);
}

function formatCommissionDate(value: unknown): string {
  const date = new Date(String(value));
  return Number.isNaN(date.getTime())
    ? "Not available"
    : new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(date);
}

function addField(container: HTMLElement, label: string, value: string): void {
  const row = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  row.append(strong, document.createTextNode(value));
  container.append(row);
}
```

- [ ] **Step 2: Implement a single reusable popup**

Create a popup with `closeButton: false`, `closeOnClick: false`, and class
name `point-hover-popup`. On `mousemove`, call:

```typescript
const features = map.queryRenderedFeatures(event.point, {
  layers: ["cms-stations", "wtg-sites"],
});
```

When no feature exists, remove the popup and reset
`map.getCanvas().style.cursor` to `""`. For a point feature, use its
longitude/latitude to set the popup location and build its content with
`setDOMContent`.

For `cms-stations`, show `State / Site Office` from `properties.site_office`.
For `wtg-sites`, show:

```typescript
addField(element, "Customer", displayValue(properties.customer_name));
addField(element, "Main site", displayValue(properties.main_site));
addField(element, "Commissioned", formatCommissionDate(properties.comm_date));
addField(element, "Installed capacity", displayValue(properties.inst_capacity));
```

Use `map.on("mousemove", handler)` and `map.on("mouseleave", handler)`.
The returned cleanup must remove both listeners, remove the popup, and reset
the cursor.

- [ ] **Step 3: Register and clean up the interaction**

In `Map.tsx`, import the helper. Immediately after `addLayers(map)`, assign:

```typescript
const detachPointHoverTooltip = attachPointHoverTooltip(map);
```

Keep a local cleanup reference in the `useEffect` closure and invoke it
before `map.remove()` in the returned cleanup function. Do not alter
`ContextMenuControl` or its right-click event.

- [ ] **Step 4: Validate TypeScript**

```powershell
npm run lint
npm run build
```

Expected: both commands succeed with no new dependencies.

- [ ] **Step 5: Commit hover discovery**

```powershell
git add frontend/src/app/lib/PointHoverTooltip.ts frontend/src/app/components/Map.tsx
git commit -m "feat: Add point hover details"
```

---

## Phase 5 — Verify the Integrated Behavior

**What you'll learn:** how direct API checks, browser behavior, and production
builds catch different failures in an interactive geospatial feature.

### Task 7: Run full gates, smoke tests, and review the final scope

**Files:**
- Modify only if required by a failing verification: files listed above.

- [ ] **Step 1: Run all backend tests and import the application**

```powershell
Set-Location backend
uv run pytest
uv run python -c "import app.main"
```

Expected: all focused tests pass and the app imports.

- [ ] **Step 2: Run frontend gates**

```powershell
Set-Location frontend
npm run lint
npm run build
```

Expected: both commands pass.

- [ ] **Step 3: Run browser validation with local services**

Start:

```powershell
Set-Location backend
uv run uvicorn app.main:app --reload
```

In another terminal:

```powershell
Set-Location frontend
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8000"
npm run dev
```

Verify all of the following:

1. A populated Inner Zones tile returns `200`,
   `application/vnd.mapbox-vector-tile`, and a non-empty body.
2. A report opened inside a known Inner Zone is `No`, names the category and
   zone, and its combined count includes the Inner Zones match.
3. A batch containing that coordinate outputs `No` and the new Inner Zone CSV
   column.
4. Animal/Bird Migratory Path and Coastal Regulatory Zone are visibly
   distinguishable from the other four categories.
5. At India overview zoom, individual WTG and CMS points appear rather than
   clusters.
6. Hovering CMS displays State / Site Office.
7. Hovering WTG displays customer, main site, readable local date without
   time, and installed capacity.
8. Right-clicking a point and right-clicking empty space both open the
   unchanged report flow.

Stop both servers after recording the findings.

- [ ] **Step 4: Review scope and whitespace**

Run:

```powershell
git diff --check dev...HEAD
git diff --name-only dev...HEAD
```

Confirm no changed file is under `backend/test_notebooks/`, no database schema
or ingestion file changed, no dependency manifest changed, and no point
click/legend/control was added.

- [ ] **Step 5: Request review and prepare the walkthrough**

Run the repository `verify` skill, request code review, and resolve all
Critical and Important findings. Then run the repository `walkthrough` skill
with the user in this order:

1. Inner Zones database contract and hard feasibility rule;
2. regular and batch PostGIS intersections;
3. MVT layer, point visibility, and hover tooltip behavior;
4. two or three comprehension questions;
5. actual git commands used.

Append the confirmed walkthrough to `docs/superpowers/walkthroughs.md` and
commit it separately:

```powershell
git add docs/superpowers/walkthroughs.md
git commit -m "docs: Log inner zones walkthrough"
```

## Expected Changed Files

| File | Purpose |
| --- | --- |
| `backend/.gitignore` | Track focused backend tests. |
| `backend/tests/conftest.py` | Make the `app` package importable in tests. |
| `backend/tests/test_tiles.py` | Database-free MVT route contract. |
| `backend/tests/test_feasibility_engine.py` | Inner Zones hard restriction behavior. |
| `backend/tests/test_report_processor.py` | Regular report intersection behavior. |
| `backend/tests/test_batch_processor.py` | Batch and CSV behavior. |
| `backend/app/api/tiles.py` | Inner Zones MVT query and route. |
| `backend/app/engine/feasibility_engine.py` | Inner Zones rule and report helpers. |
| `backend/app/processors/reports/report_processor.py` | Regular point-in-polygon query. |
| `backend/app/processors/batches/batch_processor.py` | Batched point-in-polygon query and CSV field. |
| `frontend/src/app/lib/FindZones.tsx` | Inner Zones regular report rendering. |
| `frontend/src/app/components/ReportPanelControl.tsx` | Inner Zones report styles. |
| `frontend/src/app/lib/Layerer.tsx` | Higher-contrast polygons and unclustered points. |
| `frontend/src/app/lib/PointHoverTooltip.ts` | Safe reusable point-hover popup. |
| `frontend/src/app/components/Map.tsx` | Hover interaction lifecycle registration. |
| `docs/superpowers/walkthroughs.md` | Completed user walkthrough log. |
