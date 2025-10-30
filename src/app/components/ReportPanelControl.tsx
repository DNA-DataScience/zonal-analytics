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
    background: #ffffff;
    border-radius: 12px;
    border: 1px solid rgba(15, 23, 42, 0.08);
    box-shadow: 0 6px 24px rgba(16,24,40,0.08), 0 2px 4px rgba(16,24,40,0.06);
    overflow: hidden;
    max-height: 56vh;                    /* cap total panel height */
  }
  .report-panel__header {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 14px;
    font: 600 18px/1.2 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
    color: #0f172a;
    background: #f8fafc;
    border-bottom: 1px solid #e2e8f0;
  }
  .report-panel__title {
    flex: 1;
  }
  .report-panel__close {
    appearance: none;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    color: #0f172a;
    border-radius: 8px;
    width: 28px;
    height: 28px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    transition: background 0.15s ease, border-color 0.15s ease;
    margin-left: auto;
  }
  .report-panel__close:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }
  .report-panel__body {
    flex: 1 1 auto;                      /* fill remaining height */
    min-height: 0;                        /* allow to shrink for scrolling */
    overflow: auto;                       /* scroll when content is large */
    overscroll-behavior: contain;         /* prevent scroll chaining to map */
    -webkit-overflow-scrolling: touch;    /* smoother on iOS */
    padding: 12px 14px;
    color: #334155;
    font: 400 13px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
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
  }

  hide() {
    this._container.style.display = "none";
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
