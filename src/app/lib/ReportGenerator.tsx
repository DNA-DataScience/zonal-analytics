import { getZonesAt } from "@/app/lib/FindZones";
import maplibregl from "maplibre-gl";

export interface PanelLike {
  setBodyHTML(html: string): void;
}

export class ReportGenerator {
  generate(
    panel: PanelLike,
    map: maplibregl.Map,
    lat: number,
    lng: number,
    elevation?: number | null,
  ): void {
    panel.setBodyHTML(this.buildHTML(map, lat, lng, elevation));
  }

  private buildHTML(
    map: maplibregl.Map,
    lat: number,
    lng: number,
    elevation?: number | null,
  ): string {
    const latStr = lat.toFixed(5);
    const lngStr = lng.toFixed(5);
    const elevStr =
      elevation === undefined || elevation === null || Number.isNaN(elevation)
        ? "N/A"
        : `${Math.round(elevation)} m`;
    const rules = getZonesAt(map, lng, lat, {
      layerIds: ["airport-zones"],
      zoneProperty: "zone",
      pointTolerancePx: 2,
    });
    return `
      <div class="report">
        <div>Latitude: ${latStr}</div>
        <div>Longitude: ${lngStr}</div>
        <div>Elevation: ${elevStr}</div>
        ${rules}
      </div>
    `;
  }
}
