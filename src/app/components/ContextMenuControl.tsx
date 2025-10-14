import maplibregl from "maplibre-gl";

export class ContextMenuControl implements maplibregl.IControl {
  private _map?: maplibregl.Map;
  private _container!: HTMLDivElement; // Invisible container to satisfy IControl
  private _popup?: maplibregl.Popup;

  onAdd(map: maplibregl.Map): HTMLElement {
    this._map = map;

    // Create an invisible container (this control has no visible UI)
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl";
    this._container.style.display = "none";

    // Reuse a single popup instance
    this._popup = new maplibregl.Popup({
      closeButton: true,
      closeOnClick: false,
      className: "ctxmenu-popup",
    });

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
    this._container?.remove();
    this._map = undefined;
  }

  private _onContextMenu = (e: maplibregl.MapMouseEvent) => {
    if (!this._map || !this._popup) return;

    const wrapped = e.lngLat.wrap();
    const lng = wrapped.lng;
    const lat = wrapped.lat;

    const elev = this._map.queryTerrainElevation(e.lngLat);
    const elevText = elev != null ? `${Math.round(elev)} m` : "N/A";

    const html = `
      <div>
        <div><strong>Latitude:</strong> ${lat.toFixed(5)}</div>
        <div><strong>Longitude:</strong> ${lng.toFixed(5)}</div>
        <div><strong>Elevation:</strong> ${elevText}</div>
      </div>
    `;

    this._popup.setLngLat(e.lngLat).setHTML(html).addTo(this._map);
  };
}
