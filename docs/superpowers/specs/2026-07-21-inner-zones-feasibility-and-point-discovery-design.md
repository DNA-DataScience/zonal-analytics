# Inner Zones Feasibility and Point Discovery — Design

## Purpose

Extend the Inner Zones map work so that all six regulatory categories are
legible on the map and each category blocks wind-turbine feasibility. Make
WTG sites and CMS stations visible at every zoom level and reveal their
existing data when the user hovers over a point.

This is an extension of the visual Inner Zones layer. It does not change the
database schema or ingest data.

## Decisions

1. Every Inner Zones category is a hard restriction. A coordinate inside one
   or more `"GisDB".inner_zones` polygons has combined feasibility `No`.
2. Reports explain the restriction. They include the matching category and
   zone name instead of only returning a generic blocked result.
3. WTG sites and CMS stations are always rendered as individual points.
   Clustering is removed deliberately, accepting visual density to avoid
   hiding sites at overview zooms.
4. Point details appear on hover, not click. The existing right-click report
   flow continues to work on every map location.
5. WTG commission dates display as readable local dates. Time is not shown.

## Data Contract

The existing read-only `"GisDB".inner_zones` table has 843 polygon features,
non-null `geom3857`, and these six approved `category` values:

| Category | Rows |
| --- | ---: |
| Animal/Bird Migratory Path | 7 |
| Coastal Regulatory Zone | 189 |
| Heritage | 118 |
| Reservoir | 339 |
| Sanctuary | 186 |
| Defence Protected Area | 4 |

The existing point endpoints already expose the required hover data:

| Point layer | Hover fields |
| --- | --- |
| CMS stations | `State / Site Office` |
| WTG sites | `CUSTOMER_NAME`, `MAIN_SITE`, `COMM_DATE`, `INST_CAPACITY` |

`COMM_DATE` is formatted in the browser using the viewer's local date
conventions. `INST_CAPACITY` is rendered as a numeric value.

## Backend Design

### Feasibility engine

Add `inner_zones` to the engine configuration with the six categories as its
priority list. Add an inner-zone most-restrictive helper, report builder, and
an optional fourth argument to combined feasibility functions.

If an inner-zone intersection exists, `determine_feasibility` returns
`("No", "red")` before evaluating airport, MoD, or forest rules. This makes
the regulatory decision explicit and keeps the current airport/MoD/forest
behavior unchanged when there is no Inner Zones match.

The combined report includes:

- the affected Inner Zones category and name in contributing restrictions;
- a count of matching Inner Zones; and
- a clear note that turbine placement is not feasible because of the
  matching Inner Zones restriction.

### Regular reports

`report_processor.py` gets a parameterized point-in-polygon query against
`"GisDB".inner_zones`, using `geom3857 && point_geom3857` and
`ST_Intersects`. It selects `"Name"`, `category`, `state_code`, and
`state_name`.

Each matching feature becomes an Inner Zones report item. The existing report
response preserves airport, MoD, forest, nearest-airport, and combined
sections, adding the new items without altering their shape.

### Batch reports

`batch_processor.py` gets one batched Inner Zones intersection query using
the existing JSON coordinate CTE pattern. Its results group by point ID,
participate in combined feasibility, and add a `Most Restrictive Inner Zone`
CSV column.

The batch limit, semaphore, and CSV streaming interface remain unchanged.

## Map Design

### Inner Zones polygons

Keep exactly one `inner-zones-tiles` vector source and one `inner-zones` fill
layer. Set fill opacity to `0.50` and use these higher-contrast category
fills and outlines:

| Category | Fill | Outline |
| --- | --- | --- |
| Animal/Bird Migratory Path | `#fecaca` | `#fb7185` |
| Coastal Regulatory Zone | `#fb7185` | `#e11d48` |
| Heritage | `#f43f5e` | `#be123c` |
| Reservoir | `#e11d48` | `#be123c` |
| Sanctuary | `#dc2626` | `#991b1b` |
| Defence Protected Area | `#991b1b` | `#7f1d1d` |

Use fallback fill `#f3f4f6` and outline `#9ca3af`. Insert the layer after the other
polygon fills but through `addBelowLabels`, ensuring labels remain readable
while Inner Zones are not concealed by airport, forest, or MoD fills.

### CMS and WTG points

The CMS and WTG GeoJSON sources stop requesting clustering. Their circle
layers are replaced with a single always-visible layer for each point type,
with a fixed radius and sufficient opacity at every zoom. This intentionally
renders all 9,320 WTG sites and 145 CMS stations at overview zoom.

CMS and WTG circles remain above polygon fills. Existing source fetches and
backend GeoJSON routes remain unchanged.

### Hover tooltip

Add a small map-interaction module that owns one `maplibregl.Popup`. On
pointer movement over CMS or WTG rendered features, it:

1. selects the top rendered point;
2. changes the cursor to a pointer;
3. shows a non-clickable tooltip at the feature location; and
4. removes it and restores the cursor when the pointer leaves.

Tooltip content:

| Layer | Fields |
| --- | --- |
| CMS | `State / Site Office` |
| WTG | Customer name, main site, commissioned local date, installed capacity |

Build tooltip content with DOM APIs and text nodes rather than interpolated
HTML so database values cannot execute as markup. The tooltip consumes no
click or context-menu behavior. The current context menu remains the single
entry point for generating a feasibility report.

## Errors and Edge Cases

- Empty Inner Zones intersections leave existing feasibility behavior intact.
- A null or invalid WTG commission date displays `Not available`.
- A missing installed capacity displays `Not available`.
- Hovering over overlapping CMS and WTG points displays the top rendered
  feature, matching normal MapLibre hit testing.
- If the point GeoJSON fetch fails, existing console error behavior remains;
  hover simply finds no points.

## Verification

1. Database-free backend tests cover regular and batch Inner Zones matches,
   the `No` feasibility outcome, non-matching coordinates, and CSV output.
2. Frontend checks confirm the map compiles and lint passes.
3. Browser checks confirm every category is visible in a populated region,
   all point layers render at the India overview, each tooltip has the stated
   fields and formats, and right-click reports still work over both points
   and empty map space.
4. Review the final diff to confirm no PostGIS table, ingestion notebook,
   unrelated feasibility rule, or report/batch behavior was modified.

## Out of Scope

- Database migrations, new tables, or data upload changes.
- A legend, filter control, point click popup, or new map control.
- Changing the meaning of airport, MoD, or forest rules when no Inner Zones
  restriction is present.
- Point clustering or aggregation at any zoom level.
