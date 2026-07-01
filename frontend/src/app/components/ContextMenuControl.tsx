import maplibregl from "maplibre-gl";
import { ReportPanelControl } from "@/app/components/ReportPanelControl";
import { ReportGenerator } from "@/app/lib/ReportGenerator";

export class ContextMenuControl implements maplibregl.IControl {
  private _map?: maplibregl.Map;
  private _container!: HTMLDivElement; // Invisible container to satisfy IControl
  private _popup?: maplibregl.Popup;
  private _styleEl?: HTMLStyleElement;
  private _panel: ReportPanelControl;
  private _generator: ReportGenerator;

  constructor(panel: ReportPanelControl) {
    this._panel = panel;
    this._generator = new ReportGenerator();
  }

  onAdd(map: maplibregl.Map): HTMLElement {
    this._map = map;

    // Create an invisible container (this control has no visible UI)
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl";
    this._container.style.display = "none";

    // Reuse a single popup instance
    this._popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: true,
      className: "ctxmenu-popup",
      offset: 12,
    });

    if (!document.getElementById("ctxmenu-popup-style")) {
      const style = document.createElement("style");
      style.id = "ctxmenu-popup-style";
      style.textContent = `
        .maplibregl-popup.ctxmenu-popup .ctxmenu-btn {
          padding: 8px 16px;
          border: 1px solid var(--ui-accent);
          border-radius: 9px;
          background: var(--ui-accent);
          color: #ffffff;
          font: 600 12.5px/1 system-ui,-apple-system,Segoe UI,Roboto,"Helvetica Neue",Arial,"Noto Sans","Liberation Sans";
          cursor: pointer;
          box-shadow: 0 2px 6px var(--ui-accent-ring);
          transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease, transform 0.05s ease;
        }
        .maplibregl-popup.ctxmenu-popup .ctxmenu-btn:hover {
          background: var(--ui-accent-hover);
          border-color: var(--ui-accent-hover);
          box-shadow: 0 4px 12px var(--ui-accent-ring);
        }
        .maplibregl-popup.ctxmenu-popup .ctxmenu-btn:active {
          transform: translateY(1px);
        }
        .maplibregl-popup.ctxmenu-popup .ctxmenu-btn:focus {
          outline: 2px solid #93c5fd;
          outline-offset: 2px;
        }
      `;
      document.head.appendChild(style);
      this._styleEl = style;
    }

    map.on("contextmenu", this._onContextMenu);

    return this._container;
  }

  onRemove(): void {
    if (this._map) {
      this._map.off("contextmenu", this._onContextMenu);
    }
    if (this._popup) {
      this._popup.remove();
      this._popup = undefined;
    }
    if (this._styleEl) {
      this._styleEl.remove();
      this._styleEl = undefined;
    }
    this._container?.remove();
    this._map = undefined;
  }

  public showAt(lnglat: maplibregl.LngLatLike) {
    if (!this._map || !this._popup) return;

    this._openPopupAt(maplibregl.LngLat.convert(lnglat));
  }

  private _onContextMenu = (e: maplibregl.MapMouseEvent) => {
    if (!this._map || !this._popup) return;

    this._openPopupAt(e.lngLat);
  };

  private _openPopupAt(lnglat: maplibregl.LngLat) {
    if (!this._map || !this._popup) return;

    const wrapped = lnglat.wrap();
    const lng = wrapped.lng;
    const lat = wrapped.lat;

    const elev = this._map.queryTerrainElevation(lnglat);
    const elevText = elev != null ? `${Math.round(elev)} m` : "N/A";

    const html = `
      <div>
        <div><strong>Latitude:</strong> ${lat.toFixed(5)}</div>
        <div><strong>Longitude:</strong> ${lng.toFixed(5)}</div>
        <div><strong>Elevation:</strong> ${elevText}</div>
        <div><strong>Zoom:</strong> ${this._map.getZoom().toFixed(2)}</div>
        <div style="margin-top: 8px;">
            <button type="button" class="ctxmenu-btn">Report</button>
        </div>
      </div>
    `;

    this._popup.setLngLat(lnglat).setHTML(html).addTo(this._map);

    const btn = this._popup
      .getElement()
      .querySelector(".ctxmenu-btn") as HTMLButtonElement | null;

    btn?.addEventListener("click", () => {
      if (this._map) {
        this._generator.generate(this._panel, this._map, lat, lng, elev);
      }
      this._panel.addMarker(lat, lng);
      this._panel.show();
      this._popup?.remove();
    });
  }
}
