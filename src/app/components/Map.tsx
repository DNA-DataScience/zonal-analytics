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
import { MaplibreTerradrawControl } from "@watergis/maplibre-gl-terradraw";
import "maplibre-gl/dist/maplibre-gl.css";
import "@watergis/maplibre-gl-terradraw/dist/maplibre-gl-terradraw.css";
import { CalibrationControl } from "@/app/components/CalibrationControl";
import { CalibrationMenuControl } from "@/app/components/CalibrationMenuControl";

const INDIA_BOUNDS: LngLatBoundsLike = [
  [68.17665, 6.747139], // SW [lng, lat]
  [97.40256, 35.495405], // NE [lng, lat]
];

const Map: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapType | null>(null);
  const drawRef = useRef<MaplibreTerradrawControl | null>(null);
  const calibrationRef = useRef<CalibrationControl | null>(null);
  const isInitializingRef = useRef<boolean>(false);

  useEffect(() => {
    if (mapRef.current || !mapContainerRef.current) return; // initialize only once

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: `https://tiles.openfreemap.org/styles/bright`,
      center: [78.9629, 20.5937], // India center [lng, lat]
      zoom: 4,
      renderWorldCopies: false,
      maxBounds: INDIA_BOUNDS,
    });
    mapRef.current = map;

    // const cleanupControls = () => {
    //   if (!mapRef.current) return;
    //
    //   // Clean up draw control
    //   if (drawRef.current) {
    //     try {
    //       // Check if the control is actually attached to the map
    //       const controls = mapRef.current._controls;
    //       const isAttached = controls && controls.includes(drawRef.current);
    //
    //       if (isAttached) {
    //         mapRef.current.removeControl(drawRef.current);
    //         console.log("Successfully removed draw control");
    //       } else {
    //         console.log("Draw control was not attached to map");
    //       }
    //     } catch (e) {
    //       console.warn("Failed to remove draw control:", e);
    //     } finally {
    //       drawRef.current = null;
    //     }
    //   }
    //
    //   // Clean up calibration control
    //   if (calibrationRef.current) {
    //     try {
    //       const controls = mapRef.current._controls;
    //       const isAttached =
    //         controls && controls.includes(calibrationRef.current);
    //
    //       if (isAttached) {
    //         mapRef.current.removeControl(calibrationRef.current);
    //         console.log("Successfully removed calibration control");
    //       } else {
    //         console.log("Calibration control was not attached to map");
    //       }
    //     } catch (e) {
    //       console.warn("Failed to remove calibration control:", e);
    //     } finally {
    //       calibrationRef.current = null;
    //     }
    //   }
    // };

    // const initializeControls = async () => {
    //   if (!mapRef.current || isInitializingRef.current) {
    //     console.log(
    //       "Skipping initialization - map not ready or already initializing",
    //     );
    //     return;
    //   }
    //
    //   console.log("Starting control initialization");
    //   isInitializingRef.current = true;
    //
    //   try {
    //     // Clean up existing controls first
    //     cleanupControls();
    //
    //     // Small delay to ensure cleanup is complete
    //     await new Promise((resolve) => setTimeout(resolve, 100));
    //
    //     if (!mapRef.current) {
    //       console.log("Map was removed during initialization");
    //       return;
    //     }
    //
    //     // Create new draw control
    //     const draw = new MaplibreTerradrawControl({
    //       modes: [
    //         "angled-rectangle",
    //         "select",
    //         "delete-selection",
    //         "delete",
    //         "download",
    //       ],
    //       open: true,
    //     });
    //
    //     // Add draw control
    //     mapRef.current.addControl(draw, "top-right");
    //     drawRef.current = draw;
    //     console.log("Added new draw control");
    //
    //     // Create and add calibration control
    //     const calibrationButton = new CalibrationControl(draw);
    //     mapRef.current.addControl(calibrationButton, "top-right");
    //     calibrationRef.current = calibrationButton;
    //     console.log("Added new calibration control");
    //   } catch (error) {
    //     console.error("Error during control initialization:", error);
    //   } finally {
    //     isInitializingRef.current = false;
    //   }
    // };

    map.on("load", () => {
      if (!mapRef.current) return;

      console.log("Map loaded, adding basic controls");

      map.addControl(new maplibregl.NavigationControl(), "top-right");

      const reportPanel = new ReportPanelControl();
      const contextMenuCtrl = new ContextMenuControl(reportPanel);

      map.addControl(contextMenuCtrl);
      map.addControl(new CoordinateSearchControl(contextMenuCtrl), "top-left");
      map.addControl(reportPanel, "top-left");
      map.addControl(new CoordsControl(), "bottom-left");
      map.addControl(new StyleToggleControl("bright"), "bottom-right");
      map.addControl(new CalibrationMenuControl(), "top-right");
      map.setMaxZoom(18);

      const toggle = new LayerToggleControl({
        layerId: "airport-zones",
        hiddenOpacity: 0.0001,
        label: "Airport Layers",
      });
      map.addControl(toggle, "bottom-right");

      addLayers(map);

      // Initialize drawing controls
      //initializeControls();
    });

    // // Handle style changes - reinitialize Terra Draw after style loads
    // map.on("style.load", () => {
    //   console.log("Style loaded, reinitializing Terra Draw controls");
    //   // Reinitialize Terra Draw controls after style loads
    //   setTimeout(() => {
    //     initializeControls();
    //   }, 150); // Increased delay to ensure style is fully loaded
    // });

    return () => {
      console.log("Cleaning up map and controls");
      isInitializingRef.current = false;

      if (mapRef.current) {
        //cleanupControls();
        mapRef.current.remove();
        mapRef.current = null;
      }

      drawRef.current = null;
      calibrationRef.current = null;
    };
  }, []);

  return (
    <div ref={mapContainerRef} style={{ width: "100vw", height: "100vh" }} />
  );
};

export default Map;
