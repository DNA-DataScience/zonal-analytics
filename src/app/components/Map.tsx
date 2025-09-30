"use client";
import React, { useEffect, useRef } from "react";
import maplibregl, { LngLatBoundsLike, Map as MapType } from "maplibre-gl";
import { geoCoder } from "../lib/Geocoder";
import MaplibreGeocoder from "@maplibre/maplibre-gl-geocoder";

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

      map.addControl(
        new MaplibreGeocoder(geoCoder, {
          maplibregl,
        }),
        "top-left",
      );

      //Optional zoom limit
      map.setMaxZoom(18);

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

      // Helper to safely add a layer before labels
      // const addBelowLabels = (layer: maplibregl.LayerSpecification) => {
      //     if (labelLayerId) {
      //         map.addLayer(layer, labelLayerId);
      //     } else {
      //         map.addLayer(layer);
      //     }
      // };

      // Forests (from landuse, class=forest)
      addBelowLabels(
        {
          id: "landuse-forest-fill",
          type: "fill",
          source: "openmaptiles",
          "source-layer": "landcover",
          filter: ["==", ["get", "class"], "wood"],
          minzoom: 6,
          paint: {
            "fill-color": "#1fcc31",
            "fill-opacity": [
              "interpolate",
              ["linear"],
              ["zoom"],
              5,
              0.4,
              10,
              0.6,
              14,
              0.7,
            ],
            //'fill-outline-color': '#000000', //This is costly
          },
        },
        labelLayerId,
      );

      // Military areas (from landuse, class=military)
      addBelowLabels(
        {
          id: "landuse-military-fill",
          type: "fill",
          source: "openmaptiles",
          "source-layer": "landuse",
          filter: ["==", ["get", "class"], "military"],
          minzoom: 6,
          paint: {
            "fill-color": "#e74c3c",
            "fill-opacity": [
              "interpolate",
              ["linear"],
              ["zoom"],
              5,
              0.4,
              10,
              0.6,
              14,
              0.7,
            ],
            //'fill-outline-color': '#000000', //Costly
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
