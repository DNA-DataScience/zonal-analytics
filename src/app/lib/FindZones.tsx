import maplibregl from "maplibre-gl";

type GetZoneOptions = {
  layerIds?: string[];
  zoneProperty?: string;
  pointTolerancePx?: number;
};

export function getZonesAt(
  map: maplibregl.Map,
  lng: number,
  lat: number,
  options?: GetZoneOptions,
): string {
  const layers = options?.layerIds ?? ["airport-zones"];

  const pt = map.project([lng, lat]);
  const tol = options?.pointTolerancePx ?? 2;

  const queryBox: [[number, number], [number, number]] = [
    [pt.x - tol, pt.y - tol],
    [pt.x + tol, pt.y + tol],
  ];

  let rules: string = `<div>Rule Checks:</div>`;

  const features = map.queryRenderedFeatures(queryBox, { layers });
  if (!features.length)
    return (
      rules +
      `<div>No Zones</div>` +
      `<div style="font-weight: bold; font-size: 20px; color: lawngreen">Feasibility: Feasible</div>`
    );

  let found = 0;

  let height = 350;

  let inner = 0;

  for (const f of features) {
    let z: string | undefined;
    let note: string | undefined;

    if (options?.zoneProperty) {
      const raw = f.properties?.[options.zoneProperty];
      if (typeof raw === "string") {
        const val = raw.toLowerCase();
        if (val.includes("inner")) {
          z = "Inner Zone";
          note = "No Windmills Allowed in Inner Zone";
          inner = 1;
        } else if (val.includes("middle")) {
          z = "Middle Zone";
          note =
            "Windmills need to be under height requirements in Middle Zone";
          height = Math.min(
            height,
            heightCheck(
              map,
              lng,
              lat,
              f.properties?.longitude,
              f.properties?.latitude,
            ),
          );
          inner = 2;
        } else if (val.includes("outer")) {
          z = "Outer Zone";
          note = "Outer Zones requires NOC, otherwise no restrictions";
        }
      }
    }

    if (z) {
      found = 1;
      rules += `<div>Airport: ${f.properties?.name}</div>
              <div>Zone: ${z}</div>
              <div>Note: ${note}</div>`;
    }
  }

  if (found === 0) rules += `<div>No Zones</div>`;

  if (height < 350)
    rules += `<div>Maximum Allowed Windmill Height: ${height}m</div>`;
  else rules += `<div>Maximum Allowed Windmill Height: No Restrictions</div>`;

  if (inner === 1)
    rules += `<div style="font-weight: bold; font-size: 20px; color: red">Feasibility: Not Feasible</div>`;
  else if (inner === 2)
    rules += `<div style="font-weight: bold; font-size: 20px; color: yellow">Feasibility: Feasible within Height Requirements</div>`;
  else
    rules += `<div style="font-weight: bold; font-size: 20px; color: lawngreen">Feasibility: Feasible</div>`;

  return rules;
}

function heightCheck(
  map: maplibregl.Map,
  lng: number,
  lat: number,
  airlng: number,
  airlat: number,
): number {
  const pt = new maplibregl.LngLat(lng, lat);
  const ptElev = map.queryTerrainElevation(pt);
  const airpt = new maplibregl.LngLat(airlng, airlat);
  const airptElev = map.queryTerrainElevation(airpt);
  const dist = pt.distanceTo(airpt);
  if (airptElev && ptElev) {
    console.log("Checked Elevation");
    return Math.min(airptElev + (45 + 0.05 * (dist - 4000)) - ptElev, 300);
  }
  return Math.min(45 + 0.05 * (dist - 4000), 300);
}
