import maplibregl from "maplibre-gl";

export class ReportPanelControl implements maplibregl.IControl {
  private _container!: HTMLDivElement;
  private _map?: maplibregl.Map;
  private _styleEl?: HTMLStyleElement;
  private _marker?: maplibregl.Marker;

  onAdd(map: maplibregl.Map): HTMLElement {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl report-panel";
    this._container.style.display = "none";

    if (!document.getElementById("report-panel-style")) {
      const style = document.createElement("style");
      style.id = "report-panel-style";
      style.textContent = `
  .maplibregl-ctrl.report-panel {
    width: 320px;
    margin: 8px 0 0 8px;
  }
  .report-panel__card {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    max-height: 60vh;
  }
  .report-panel__body {
    flex: 1 1 auto;
    min-height: 0;
    overflow: auto;
    padding: 14px 16px;
    color: #334155;
    font: 400 13px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
  }

  /* Feasibility Badges */
  .badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.2;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }
  .badge-no {
    background: #fee;
    color: #dc2626;
    border: 1px solid #fca5a5;
  }
  .badge-noc {
    background: #fef3c7;
    color: #d97706;
    border: 1px solid #fcd34d;
  }
  .badge-yes {
    background: #dcfce7;
    color: #16a34a;
    border: 1px solid #86efac;
  }
  .badge-unknown {
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
  }
  .badge-small {
    padding: 3px 8px;
    font-size: 11px;
  }

  /* Report Sections */
  .report-section {
    margin-bottom: 16px;
    padding-bottom: 16px;
    border-bottom: 1px solid #e2e8f0;
  }
  .report-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
    padding-bottom: 0;
  }

  /* Combined Analysis Section */
  .combined-section {
    background: #f8fafc;
    padding: 14px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }
  .combined-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  .combined-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #0f172a;
  }
  .combined-note {
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.5;
    color: #475569;
  }
  .restrictions-section {
    margin-top: 12px;
  }
  .restrictions-section h4 {
    margin: 0 0 6px 0;
    font-size: 13px;
    font-weight: 600;
    color: #334155;
  }
  .contributing-restrictions {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .contributing-restrictions li {
    padding: 4px 0;
    font-size: 12px;
    color: #475569;
    display: flex;
    align-items: flex-start;
    gap: 6px;
  }
  .restriction-dot {
    font-size: 10px;
    line-height: 1.5;
  }
  .no-restrictions {
    font-size: 12px;
    color: #64748b;
    font-style: italic;
    margin: 4px 0;
  }

  /* Zone Count Badges */
  .zone-counts {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 8px 0;
  }
  .count-badge {
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    background: #f1f5f9;
    color: #475569;
    border: 1px solid #cbd5e1;
  }
  .count-airport {
    background: #e0e7ff;
    color: #4338ca;
    border-color: #c7d2fe;
  }
  .count-mod {
    background: #fee2e2;
    color: #dc2626;
    border-color: #fca5a5;
  }
  .count-forest {
    background: #dcfce7;
    color: #15803d;
    border-color: #86efac;
  }
  .count-inner-zones {
    background: #ffe4e6;
    color: #be123c;
    border-color: #fda4af;
  }

  /* Section Headers with Collapsible */
  .zone-section {
    margin-top: 12px;
  }
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    cursor: pointer;
    user-select: none;
    transition: background 0.15s ease;
  }
  .section-header:hover {
    background: #f1f5f9;
  }
  .section-title {
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
  }
  .section-count {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    background: #e2e8f0;
    color: #475569;
  }

  /* Collapsible Details */
  .zone-details {
    border: none;
  }
  .zone-details summary {
    list-style: none;
  }
  .zone-details summary::-webkit-details-marker {
    display: none;
  }
  .zone-details summary::before {
    content: '▶';
    display: inline-block;
    margin-right: 6px;
    font-size: 10px;
    transition: transform 0.2s ease;
  }
  .zone-details[open] summary::before {
    transform: rotate(90deg);
  }

  /* Zone Cards Container */
  .zone-cards {
    margin-top: 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  /* Zone Card */
  .zone-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    transition: box-shadow 0.2s ease;
  }
  .zone-card:hover {
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  .zone-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    gap: 8px;
  }
  .zone-card-title {
    margin: 0;
    font-size: 14px;
    font-weight: 600;
    color: #0f172a;
    flex: 1;
  }
  .nearest-label {
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    background: #f1f5f9;
    color: #64748b;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.025em;
  }
  .zone-card-body {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .zone-field {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    font-size: 12px;
  }
  .field-label {
    font-weight: 600;
    color: #475569;
    min-width: 90px;
    flex-shrink: 0;
  }
  .field-value {
    color: #334155;
    flex: 1;
  }
  .zone-note .field-label {
    align-self: flex-start;
  }
  .zone-note .field-value {
    line-height: 1.5;
  }
  .auto-settle {
    font-size: 12px;
    color: #64748b;
  }

  /* Card Type Variants */
  .airport-card {
    border-left: 3px solid #4338ca;
  }
  .mod-card {
    border-left: 3px solid #dc2626;
  }
  .forest-card {
    border-left: 3px solid #15803d;
  }
  .inner-zones-card {
    border-left: 3px solid #be123c;
  }
  .forest-card .zone-card-header {
    margin-bottom: 0;
  }

  /* Empty State */
  .empty-state {
    padding: 16px;
    text-align: center;
    color: #16a34a;
    font-size: 13px;
    font-weight: 500;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 6px;
    margin-top: 10px;
  }

  /* Legacy Format Support */
  .rules {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  .rules li {
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e2e8f0;
  }
  .rules li:last-child {
    border-bottom: none;
  }
  .airport-info {
    margin: 8px 0 0 16px;
    display: grid;
    grid-template-columns: max-content 1fr;
    column-gap: 8px;
    row-gap: 4px;
  }
  .airport-info dt,
  .airport-info dd {
    margin: 0;
    font-size: 12px;
  }
  .airport-info dt {
    color: #64748b;
  }
  .airport-info dd {
    color: #334155;
  }
`;
      document.head.appendChild(style);
      this._styleEl = style;
    }

    this._container.innerHTML = `
      <div class="report-panel__card" role="region" aria-label="Report panel">
        <div class="report-panel__header">
          <div class="report-panel__title">Feasibility Report</div>
          <button type="button" class="report-panel__close" aria-label="Close panel" title="Close">×</button>
        </div>
        <div class="report-panel__body"></div>
      </div>
    `;

    const closeBtn = this._container.querySelector(
      ".report-panel__close",
    ) as HTMLButtonElement | null;
    closeBtn?.addEventListener("click", () => this.hide());

    return this._container;
  }

  onRemove() {
    this._container?.remove();
    this._map = undefined;
    if (this._styleEl) {
      this._styleEl.remove();
      this._styleEl = undefined;
    }
    if (this._marker) {
      this._marker?.getPopup()?.remove();
      this._marker.remove();
      this._marker = undefined;
    }
  }

  addMarker(lat: number, lng: number) {
    if (this._map instanceof maplibregl.Map) {
      if (this._marker) {
        this._marker.getPopup()?.remove();
        this._marker.remove();
        this._marker = undefined;
      }
      this._marker = new maplibregl.Marker()
        .setLngLat([lng, lat])
        .addTo(this._map);
    }
  }

  show() {
    this._container.style.display = "";
    this._container.classList.add("open");
  }

  hide() {
    this._container.style.display = "none";
    this._container.classList.remove("open");
    this._marker?.getPopup()?.remove();
    this._marker?.remove();
    this._marker = undefined;
  }

  setBodyHTML(html: string) {
    const body = this._container.querySelector(
      ".report-panel__body",
    ) as HTMLElement | null;
    if (body) {
      body.innerHTML = html;
    }
  }
}
