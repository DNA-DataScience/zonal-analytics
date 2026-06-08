import maplibregl from "maplibre-gl";

export function addLayers(map: maplibregl.Map) {
  const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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
      tiles: [`${apiBaseUrl}/tiles/airport/{z}/{x}/{y}.mvt`],
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
          "#ddbe36", // Yellow
          "outer",
          "#c6ed3b", // Green
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
          "#c1a122", // Dark yellow
          "outer",
          "#caf411", // Dark green
          "funnel",
          "#7f1d1d", // Dark red
          "#6b7280", // Default dark gray
        ],
      },
    },
    labelLayerId,
  );

  if (!map.getSource("forest-tiles")) {
    console.log("Adding forest tiles");
    map.addSource("forest-tiles", {
      type: "vector",
      tiles: [`${apiBaseUrl}/tiles/forest/{z}/{x}/{y}.mvt`],
      minzoom: 0,
      maxzoom: 15,
    });
  }

  // Forest polygons are a single category, so use one consistent fill style.
  addBelowLabels(
    {
      id: "forest-zones",
      type: "fill",
      source: "forest-tiles",
      "source-layer": "reserve_forests",
      paint: {
        "fill-color": "#f43f5e",
        "fill-opacity": 0.35,
        "fill-outline-color": "#be123c",
      },
    },
    labelLayerId,
  );

  if (!map.getSource("mod-tiles")) {
    console.log("Adding mod tiles");
    map.addSource("mod-tiles", {
      type: "vector",
      tiles: [`${apiBaseUrl}/tiles/mod/{z}/{x}/{y}.mvt`],
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

  // Add CMS tiles with clustering
  if (!map.getSource("cms-tiles")) {
    console.log("Adding CMS tiles");
    map.addSource("cms-tiles", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      cluster: true,
      clusterMaxZoom: 14,
      clusterRadius: 50,
    });

    // Fetch and load CMS data from GeoJSON endpoint
    fetch(`${apiBaseUrl}/points/cms.geojson`)
      .then((res) => res.json())
      .then((data) => {
        if (map.getSource("cms-tiles")) {
          (map.getSource("cms-tiles") as maplibregl.GeoJSONSource).setData(
            data,
          );
        }
      })
      .catch((err) => console.error("Failed to load CMS data:", err));
  }

  // CMS clustered points - map.addLayer without beforeId so they render on top of basemap fills
  map.addLayer({
    id: "cms-clusters",
    type: "circle",
    source: "cms-tiles",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": "#d946ef", // Bright magenta
      "circle-radius": ["step", ["get", "point_count"], 10, 50, 16, 300, 22],
      "circle-opacity": 0.85,
      "circle-stroke-width": 2,
      "circle-stroke-color": "#a61e8e", // Dark magenta
      "circle-stroke-opacity": 1,
    },
  });

  // CMS cluster count labels
  map.addLayer({
    id: "cms-cluster-count",
    type: "symbol",
    source: "cms-tiles",
    filter: ["has", "point_count"],
    layout: {
      "text-field": "{point_count_abbreviated}",
      "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
      "text-size": 12,
    },
    paint: {
      "text-color": "#ffffff",
    },
  });

  // CMS unclustered individual points
  map.addLayer({
    id: "cms-stations",
    type: "circle",
    source: "cms-tiles",
    filter: ["!", ["has", "point_count"]],
    paint: {
      "circle-radius": 6,
      "circle-color": "#d946ef", // Bright magenta
      "circle-opacity": 0.85,
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#a61e8e", // Dark magenta
      "circle-stroke-opacity": 1,
    },
  });

  // Add WTG tiles with clustering
  if (!map.getSource("wtg-tiles")) {
    console.log("Adding WTG tiles");
    map.addSource("wtg-tiles", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] },
      cluster: true,
      clusterMaxZoom: 14,
      clusterRadius: 50,
    });

    // Fetch and load WTG data from GeoJSON endpoint
    fetch(`${apiBaseUrl}/points/wtg.geojson`)
      .then((res) => res.json())
      .then((data) => {
        if (map.getSource("wtg-tiles")) {
          (map.getSource("wtg-tiles") as maplibregl.GeoJSONSource).setData(
            data,
          );
        }
      })
      .catch((err) => console.error("Failed to load WTG data:", err));
  }

  // WTG clustered points - map.addLayer without beforeId so they render on top of basemap fills
  map.addLayer({
    id: "wtg-clusters",
    type: "circle",
    source: "wtg-tiles",
    filter: ["has", "point_count"],
    paint: {
      "circle-color": "#06b6d4", // Bright cyan
      "circle-radius": ["step", ["get", "point_count"], 10, 50, 16, 300, 22],
      "circle-opacity": 0.85,
      "circle-stroke-width": 2,
      "circle-stroke-color": "#0369a1", // Dark cyan
      "circle-stroke-opacity": 1,
    },
  });

  // WTG cluster count labels
  map.addLayer({
    id: "wtg-cluster-count",
    type: "symbol",
    source: "wtg-tiles",
    filter: ["has", "point_count"],
    layout: {
      "text-field": "{point_count_abbreviated}",
      "text-font": ["Open Sans Semibold", "Arial Unicode MS Bold"],
      "text-size": 12,
    },
    paint: {
      "text-color": "#ffffff",
    },
  });

  // WTG unclustered individual points
  map.addLayer({
    id: "wtg-sites",
    type: "circle",
    source: "wtg-tiles",
    filter: ["!", ["has", "point_count"]],
    paint: {
      "circle-radius": 6,
      "circle-color": "#06b6d4", // Bright cyan
      "circle-opacity": 0.85,
      "circle-stroke-width": 1.5,
      "circle-stroke-color": "#0369a1", // Dark cyan
      "circle-stroke-opacity": 1,
    },
  });
}
