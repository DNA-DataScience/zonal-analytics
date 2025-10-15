export interface PanelLike {
  setBodyHTML(html: string): void;
}

export type ReportInput = {
  lat: number;
  lng: number;
  elevation?: number | null;
};

export class ReportGenerator {
  generate(panel: PanelLike, { lat, lng, elevation }: ReportInput): void {
    panel.setBodyHTML(this.buildHTML(lat, lng, elevation));
  }

  private buildHTML(
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

    return `
      <div class="report">
        <div>Latitude: ${latStr}</div>
        <div>Longitude: ${lngStr}</div>
        <div>Elevation: ${elevStr}</div>
      </div>
    `;
  }
}
