"use client";
import React, { useEffect, useRef } from "react";
import maplibregl, { LngLatBoundsLike, Map as MapType } from "maplibre-gl";
import { CoordsControl } from "@/app/components/CoordsControl";
import { ContextMenuControl } from "@/app/components/ContextMenuControl";
import { ReportPanelControl } from "@/app/components/ReportPanelControl";
import { CoordinateSearchControl } from "@/app/components/CoordinateSearchControl";
import { StyleToggleControl } from "@/app/components/StyleToggleControl";
import { addLayers } from "@/app/lib/Layerer";
import { LayerToggleControl } from "@/app/components/LayerToggleControl";

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
      style: `https://tiles.openfreemap.org/styles/bright`,
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

      map.addControl(new CoordsControl(), "bottom-left");
      map.addControl(new StyleToggleControl("bright"), "bottom-right");

      //Optional zoom limit
      map.setMaxZoom(18);

      const toggle = new LayerToggleControl({
        layerId: "airport-zones",
        hiddenOpacity: 0.0001,
        label: "Airport Layers",
      });
      map.addControl(toggle, "bottom-right");

      addLayers(map);
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
