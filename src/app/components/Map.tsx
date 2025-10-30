"use client";
import React, { useEffect, useRef } from "react";
import maplibregl, { LngLatBoundsLike, Map as MapType } from "maplibre-gl";
// import { geoCoder } from "../lib/Geocoder";
// import MaplibreGeocoder, {
//   CarmenGeojsonFeature,
// } from "@maplibre/maplibre-gl-geocoder";
import { CoordsControl } from "@/app/components/CoordsControl";
import { ContextMenuControl } from "@/app/components/ContextMenuControl";
import { ReportPanelControl } from "@/app/components/ReportPanelControl";
import { CoordinateSearchControl } from "@/app/components/CoordinateSearchControl";

const INDIA_BOUNDS: LngLatBoundsLike = [
  [68.17665, 6.747139], // SW [lng, lat]
  [97.40256, 35.495405], // NE [lng, lat]
];

const Map: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapType | null>(null);

  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return; // initialize only once

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      // You can get a free key from https://www.maptiler.com/
      // I recommend storing it in an environment variable.
      style: `https://tiles.openfreemap.org/styles/liberty`,
      center: [78.9629, 20.5937], // India center [lng, lat]
      zoom: 4,
      // pitch: 45,
      // bearing: -17.6,
      //Performance helpers to load only India on map:
      renderWorldCopies: false,
      maxBounds: INDIA_BOUNDS,
      // crossSourceCollisions: false,
    });
    mapRef.current = map;

    map.on("load", () => {
      if (!mapRef.current) return;

      map.addControl(new maplibregl.NavigationControl(), "top-right");

      const reportPanel = new ReportPanelControl();
      const contextMenuCtrl = new ContextMenuControl(reportPanel);

      // Add right-click context menu popup
      map.addControl(contextMenuCtrl);

      map.addControl(new CoordinateSearchControl(contextMenuCtrl), "top-left");
      map.addControl(reportPanel, "top-left");

      // const geocoderControl = new MaplibreGeocoder(geoCoder, {
      //   maplibregl,
      //   zoom: 14,
      //   flyTo: {
      //     padding: 15,
      //     easing: (t: number) => {
      //       return t;
      //     },
      //     zoom: 14,
      //   },
      // });
      //
      // map.addControl(geocoderControl, "top-left");

      map.addControl(new CoordsControl(), "bottom-left");

      //Optional zoom limit
      map.setMaxZoom(18);

      map.addSource("dem", {
        type: "raster-dem",
        tiles: [
          "https://elevation-tiles-prod.s3.amazonaws.com/terrarium/{z}/{x}/{y}.png",
        ], // encoding: 'terrarium'
        //tiles: ["https://tiles.openfreemap.org/tiles/srtm_30m/{z}/{x}/{y}.png"],
        tileSize: 256,
        maxzoom: 14,
        encoding: "terrarium",
      });

      map.setTerrain({ source: "dem", exaggeration: 1.0 });

      const layers = map.getStyle().layers;
      let labelLayerId = "";
      for (const layer of layers) {
        if (
          layer.type === "symbol" &&
          layer.layout &&
          layer.layout["text-field"]
        ) {
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

      map.addSource("airport-tiles", {
        type: "vector",
        tiles: ["http://127.0.0.1:8000/tiles/{z}/{x}/{y}.mvt"],
        minzoom: 0,
        maxzoom: 15,
      });

      addBelowLabels(
        {
          id: "airport-zones",
          type: "fill",
          source: "airport-tiles",
          "source-layer": "airport_layers",
          filter: [
            "all",
            [
              "any",
              ["!=", ["get", "type"], "closed"],
              [
                "all",
                ["==", ["get", "type"], "closed"],
                ["==", ["get", "zone"], "inner"],
              ],
            ],
          ],
          layout: {
            "fill-sort-key": [
              "case",
              ["==", ["get", "type"], "closed"],
              0,
              [
                "match",
                ["get", "zone"],
                "outer",
                1,
                "middle",
                2,
                "inner",
                3,
                1,
              ],
            ],
          },
          paint: {
            "fill-color": [
              "case",
              ["==", ["get", "type"], "closed"],
              "#9ca3af",
              [
                "match",
                ["get", "zone"],
                "inner",
                "#ef4444",
                "middle",
                "#f59e0b",
                "outer",
                "#22c55e",
                "#9ca3af",
              ],
            ],
            "fill-opacity": [
              "interpolate",
              ["linear"],
              ["zoom"],
              5,
              0.1,
              10,
              0.2,
              14,
              0.4,
              16,
              0.6,
            ],
            "fill-outline-color": [
              "case",
              ["==", ["get", "type"], "closed"],
              "#6b7280",
              [
                "match",
                ["get", "zone"],
                "inner",
                "#7f1d1d",
                "middle",
                "#92400e",
                "outer",
                "#166534",
                "#6b7280",
              ],
            ],
          },
        },
        labelLayerId,
      );
    });

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, []);

  return (
    <div ref={mapContainerRef} style={{ width: "100vw", height: "100vh" }} />
  );
};

export default Map;
