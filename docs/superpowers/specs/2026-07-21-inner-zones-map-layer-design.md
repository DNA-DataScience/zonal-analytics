# Inner Zones Map Layer — Design

**Date:** 2026-07-21  
**Status:** Approved  
**Scope:** Visual-only map layer

## Goal

Show the six uploaded inner-zone categories on the main MapLibre map. Users should see the zones as default-visible polygon overlays, with related red shades that distinguish categories without competing with the existing airport, forest, and Ministry of Defence layers.

## Context

The ingestion work has successfully created the PostGIS table `"GisDB".inner_zones`. Its canonical `geometry` column is a two-dimensional `MultiPolygon` in EPSG:4326, and `geom3857` is its Web Mercator tile geometry with a GiST index. The table contains only polygonal features in these categories:

- `Animal/Bird Migratory Path`
- `Coastal Regulatory Zone`
- `Defence Protected Area`
- `Heritage`
- `Reservoir`
- `Sanctuary`

The data-upload notebook is exploratory and already succeeded. This feature consumes the uploaded table; it does not reprocess or reload source data.

## Decisions

| Area               | Decision                                                | Why                                                                                                                                     |
| ------------------ | ------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Product scope      | Map display only                                        | The categories do not yet have feasibility rules, so reports and batch results must remain unchanged.                                   |
| API shape          | `GET /tiles/inner-zones/{z}/{x}/{y}.mvt`                | Matches existing MVT tile endpoints and keeps viewport-sized data transfers efficient.                                                  |
| Backend home       | Add the query and handler to `backend/app/api/tiles.py` | That router already owns all MVT endpoints and is registered by `backend/app/main.py`.                                                  |
| Tile layer name    | `inner_zones`                                           | Matches the database table and is the MapLibre `source-layer` name.                                                                     |
| Tile properties    | `Name`, `category`, `state_code`, and `state_name`      | Preserves category styling and enough future-safe context without passing the full source description into every tile.                  |
| Database geometry  | Query `geom3857` only                                   | `ST_TileEnvelope` is Web Mercator, so this avoids transforming geometry for every request.                                              |
| Rendering model    | One vector source and one category-driven fill layer    | A MapLibre `match` expression gives six shades from one downloaded dataset and avoids six duplicate source requests.                    |
| Default state      | Visible when the map opens                              | Approved user preference; follows current airport, forest, and MoD layer behavior.                                                      |
| Controls           | No new layer toggle                                     | The existing toggle component only controls a single fill layer and is not currently used to manage the existing default-visible zones. |
| Layer placement    | Below labels                                            | Preserves place-name readability and matches the existing zone fill ordering.                                                           |
| Feasibility engine | No `LAYER_CONFIG` or report-processor changes           | The user approved visual-only scope.                                                                                                    |

## API Contract

The backend will produce Mapbox Vector Tile bytes from `"GisDB".inner_zones`.

- Route: `/tiles/inner-zones/{z}/{x}/{y}.mvt`
- Content type: `application/vnd.mapbox-vector-tile`
- Vector layer: `inner_zones`
- Maximum zoom: use the existing `MAX_ZOOM = 15`; return HTTP 204 beyond it.
- Empty viewport tile: return an empty MVT response with the same content type.
- Database protection: reuse the existing `TILE_SEMAPHORE`.
- Spatial selection: use `geom3857 && ST_TileEnvelope(:z, :x, :y)` before `ST_AsMVTGeom`.

The route exposes map-display fields only. It must not return the full `Description` field because it may contain large, inconsistent source HTML and is not needed for the first map layer.

## Visual Design

The frontend will register `inner-zones-tiles` and the `inner-zones` fill layer in `frontend/src/app/lib/Layerer.tsx`. The fill color uses a `match` expression on `category`; outlines use a darker match expression. The recommended palette intentionally ranges from pale to strong red:

| Category                   | Fill      | Outline   |
| -------------------------- | --------- | --------- |
| Animal/Bird Migratory Path | `#fee2e2` | `#fca5a5` |
| Coastal Regulatory Zone    | `#fecaca` | `#fb7185` |
| Heritage                   | `#fda4af` | `#f43f5e` |
| Reservoir                  | `#fb7185` | `#e11d48` |
| Sanctuary                  | `#f87171` | `#dc2626` |
| Defence Protected Area     | `#ef4444` | `#991b1b` |

Use moderate transparency (initially `fill-opacity: 0.32`) so overlapping boundaries and the basemap remain readable. Use a neutral fallback fill and outline for unexpected categories, rather than failing to draw a feature.

## Validation and Failure Handling

Before coding, confirm the upload’s schema and categories through a read-only database query. Verify the table has non-null `geom3857`, all six expected categories, and only polygonal geometries. Do not rerun the notebook’s replacement upload during this work.

The implementation must preserve current tile behavior: route errors become HTTP 500 responses, empty tiles are valid responses, and tiles above zoom 15 produce 204. Backend and frontend verification must run after the code changes. Since there is no complete existing test suite, add focused route tests using a fake async database session where practical and supplement them with a live local tile smoke check against the uploaded database.

## Out of Scope

- Changing feasibility decisions, point reports, batch reports, or CSV output.
- Creating per-category toggles, legends, feature popups, or search.
- Re-ingesting, changing, or replacing `"GisDB".inner_zones`.
- Changing the source KML/KMZ or the Forest notebook’s geometry conversion.
- Adding migrations or changing database credentials.

## Acceptance Criteria

1. A valid MVT request to the new endpoint reads from `"GisDB".inner_zones` and carries `category` for each feature.
2. The map requests and displays inner zones by default beneath labels.
3. The six expected categories render in distinct, related red shades; an unknown category has a safe fallback style.
4. Existing airport, forest, MoD, CMS, and WTG layers continue to load.
5. No feasibility/report code changes are introduced.
6. Backend verification and frontend lint/build gates pass, with actual results recorded before completion.
