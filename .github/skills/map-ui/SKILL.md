---
name: map-ui
description: Frontend patterns for zonal-analytics — MapLibre IControl widgets, Map.tsx registration, layer wiring via Layerer.tsx, API URL and analytics conventions. Use for any frontend/ or map UI task.
---

# Map UI Patterns

Next.js 15 App Router + React 19 + MapLibre GL 5. TypeScript strict.
Imports use the `@/` alias → `frontend/src/` (e.g. `@/app/lib/Layerer`).

## Anatomy of a map widget (IControl)

Widgets are plain classes implementing MapLibre's `IControl`, one per file in
`src/app/components/`, PascalCase names ending in `Control`:

```tsx
import maplibregl, { IControl, Map as MapType } from "maplibre-gl";

export class ExampleControl implements IControl {
  private container: HTMLDivElement | null = null;
  private map: MapType | null = null;

  onAdd(map: MapType): HTMLElement {
    this.map = map;
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    // build DOM, attach listeners here
    return this.container;
  }

  onRemove(): void {
    this.container?.remove();
    this.container = null;
    this.map = null;
  }
}
```

Register inside `map.on("load", ...)` in `src/app/components/Map.tsx`:
`map.addControl(new ExampleControl(), "top-right");`
Study `ReportPanelControl.tsx` (panel) and `BatchProcessingControl.tsx`
(complex flow) as references.

## API base URL

Always: `const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";`
Known debt: this is duplicated per file — if touching several call sites,
prefer extracting `src/app/lib/config.ts` and importing from it.

## Layers

All vector-tile sources/layers are wired in `src/app/lib/Layerer.tsx`
(`addLayers(map)`), pointing at backend `/tiles/...` routes. Add new layers
there, following the existing source/layer id naming.

## Analytics

Track user actions with `trackEvent(eventType, endpoint, metadata)` from
`@/app/lib/analytics` — see `Map.tsx` `map_interaction` example.

## Non-obvious constraints

- Map is bounded to India (`INDIA_BOUNDS` in Map.tsx), max zoom 15
- Basemap comes from `tiles.openfreemap.org` — no key, don't change casually
- `src/middleware.ts` applies Basic Auth when `BASIC_AUTH_PASS` is set
- No test framework: verify = `npm run lint` + `npm run build`
