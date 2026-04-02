import maplibregl from "maplibre-gl";

export function addLayers(map: maplibregl.Map) {
  const layers = map.getStyle().layers;
  let labelLayerId = "";
  for (const layer of layers) {
    if (layer.type === "symbol" && layer.layout && layer.layout["text-field"]) {
      labelLayerId = layer.id;
      break;
    }
  }

  const addBelowLabels = (
    layer: maplibregl.LayerSpecification,
    beforeId?: string,
  ) => {
    if (beforeId) map.addLayer(layer, beforeId);
    else map.addLayer(layer);
  };

  if (!map.getSource("dem")) {
    console.log("Adding DEM source");
    map.addSource("dem", {
      type: "raster-dem",
      tiles: [
        "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png",
      ],
      tileSize: 256,
      maxzoom: 14,
      encoding: "terrarium",
    });
  }

  map.setTerrain({ source: "dem", exaggeration: 1.0 });

  // Add state boundaries
  addBelowLabels(
    {
      id: "state-boundaries",
      type: "line",
      source: "openmaptiles",
      "source-layer": "boundary",
      // filter: ['==', 'admin_level', 4],
      filter: [
        "all",
        ["==", ["to-string", ["get", "admin_level"]], "4"],
        ["!=", ["get", "maritime"], 1],
        ["!=", ["get", "disputed"], 1],
      ],
      paint: {
        "line-color": "#4A5568", // A shade of gray
        "line-width": [
          "interpolate",
          ["linear"],
          ["zoom"],
          4,
          0.6,
          8,
          1.2,
          12,
          2,
          16,
          3,
        ],
        "line-dasharray": [2, 1],
      },
    },
    labelLayerId,
  );

  if (!map.getSource("airport-tiles")) {
    console.log("Adding airport tiles");
    map.addSource("airport-tiles", {
      type: "vector",
      tiles: ["http://127.0.0.1:8000/tiles/airport/{z}/{x}/{y}.mvt"],
      minzoom: 0,
      maxzoom: 15,
    });
  }

  // Airport zones (keep original opacity and colors)
  addBelowLabels(
    {
      id: "airport-zones",
      type: "fill",
      source: "airport-tiles",
      "source-layer": "airport_layers",
      layout: {
        "fill-sort-key": [
          "match",
          ["get", "zone"],
          "outer",
          1,
          "middle",
          2,
          "inner",
          3,
          "funnel",
          4,
          1,
        ],
      },
      paint: {
        "fill-color": [
          "match",
          ["get", "zone"],
          "inner",
          "#ef4444", // Red
          "middle",
          "#f4da50", // Yellow
          "outer",
          "#33ef04", // Green
          "funnel",
          "#ef4444", // Red
          "#9ca3af", // Default gray
        ],
        "fill-opacity": 0.4,
        "fill-outline-color": [
          "match",
          ["get", "zone"],
          "inner",
          "#7f1d1d", // Dark red
          "middle",
          "#c1a92e", // Dark yellow
          "outer",
          "#23ac02", // Dark green
          "funnel",
          "#7f1d1d", // Dark red
          "#6b7280", // Default dark gray
        ],
      },
    },
    labelLayerId,
  );

  if (!map.getSource("mod-tiles")) {
    console.log("Adding mod tiles");
    map.addSource("mod-tiles", {
      type: "vector",
      tiles: ["http://127.0.0.1:8000/tiles/mod/{z}/{x}/{y}.mvt"],
      minzoom: 0,
      maxzoom: 15,
    });
  }

  // Mod zones with very different colors and low opacity
  addBelowLabels(
    {
      id: "mod-zones",
      type: "fill",
      source: "mod-tiles",
      "source-layer": "mod_layers",
      layout: {
        "fill-sort-key": [
          "match",
          ["get", "zone"],
          ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"],
          4,
          "NO_WTG",
          3,
          "NOC",
          2,
          "NO_NOC",
          1,
          1,
        ],
      },
      paint: {
        "fill-color": [
          "match",
          ["get", "zone"],
          ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"],
          "#8f25ed", // Bright purple - very different from airport colors
          "NO_WTG",
          "#dc3535", // Bright orange - different from airport red
          "NOC",
          "#f8ba35", // Cyan - different from airport yellow
          "NO_NOC",
          "#2bef24", // Emerald - different from airport green
          "#64748b", // Slate gray
        ],
        "fill-opacity": 0.4,
        "fill-outline-color": [
          "match",
          ["get", "zone"],
          ["SPECIAL_ALLOWED", "SPECIAL_LIMITED_HEIGHT"],
          "#731cc1", // Dark purple
          "NO_WTG",
          "#c12c2c", // Dark orange
          "NOC",
          "#cd9929", // Dark cyan
          "NO_NOC",
          "#1bbc3a", // Dark emerald
          "#475569", // Dark slate
        ],
      },
    },
    labelLayerId,
  );
}
