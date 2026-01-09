import { renderZonesFromJson } from "@/app/lib/FindZones";
import maplibregl from "maplibre-gl";

export interface PanelLike {
  setBodyHTML(html: string): void;
}

export class ReportGenerator {
  async generate(
    panel: PanelLike,
    map: maplibregl.Map,
    lat: number,
    lng: number,
    elevation?: number | null,
  ): Promise<void> {
    panel.setBodyHTML(await this.buildHTML(map, lat, lng, elevation));
  }

  private async buildHTML(
    map: maplibregl.Map,
    lat: number,
    lng: number,
    elevation?: number | null,
  ): Promise<string> {
    const latStr = lat.toFixed(5);
    const lngStr = lng.toFixed(5);
    const elevStr =
      elevation === undefined || elevation === null || Number.isNaN(elevation)
        ? "N/A"
        : `${Math.round(elevation)} m`;

    // Default to empty; we'll try the backend first and fall back to local rules if needed
    let rules = "";

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/report-generator?lat=${lat}&lng=${lng}&elev=${elevation ?? 0}`,
        {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
          },
        },
      );

      if (res.ok) {
        const json = await res.json();
        console.log("Backend response: ", json);
        rules = renderZonesFromJson(json);
      } else {
        console.warn("Backend responded with status:", res.status);
      }
    } catch (e) {
      console.warn("Backend fetch failed, using local rules.", e);
    }

    return `
      <div class="report">
        <style>
          /* Indent airports under "Rule Checks" */
          .report .rule-checks > * { margin-left: 16px; }

          /* Put Zone/Note on the same line and indent them further */
          .report .rule-checks dl {
            margin: 4px 0 8px 16px;
            display: grid;
            grid-template-columns: max-content 1fr;
            column-gap: 8px;
          }
          .report .rule-checks dt,
          .report .rule-checks dd {
            margin: 0;
          }
          .report .nearest-airport > * { margin-left: 16px; }

          /* Put Zone/Note on the same line and indent them further */
          .report .nearest-airport dl {
            margin: 4px 0 8px 16px;
            display: grid;
            grid-template-columns: max-content 1fr;
            column-gap: 8px;
          }
          .report .nearest-airport dt,
          .report .nearest-airport dd {
            margin: 0;
          }
        </style>

        <div><strong>Latitude:</strong> ${latStr}</div>
        <div><strong>Longitude:</strong> ${lngStr}</div>
        <div><strong>Elevation:</strong> ${elevStr}</div>

        <div><strong>Rule Checks:</strong></div>
        <div class="rule-checks">
          ${rules}
        </div>
    `;
  }
}
