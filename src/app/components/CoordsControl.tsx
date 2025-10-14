import maplibregl from "maplibre-gl";

export class CoordsControl implements maplibregl.IControl {
  private _container!: HTMLDivElement;
  private _label!: HTMLDivElement;
  private _map?: maplibregl.Map;

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._label = document.createElement("div");
    this._label.style.padding = "6px 8px";
    this._label.style.fontSize = "12px";
    this._label.style.lineHeight = "1";
    this._label.style.backgroundColor = "#fff";
    this._label.style.borderRadius = "2px";
    this._label.style.boxShadow =
      "0 1px 2px rgba(0, 0, 0, 0.10), 0 2px 4px rgba(0, 0, 0, 0.05)";
    this._label.style.whiteSpace = "nowrap";
    this._label.style.userSelect = "none";
    this._label.style.cursor = "default";
    this._label.style.pointerEvents = "none";
    this._label.style.fontFamily = "sans-serif";
    this._label.style.textAlign = "center";
    this._label.style.color = "#000";
    this._label.textContent = "Lat: —, Lng: —, Elev: —";

    this._container.appendChild(this._label);
    map.on("mousemove", this._onMouseMove);

    return this._container;
  }

  onRemove() {
    if (this._map) {
      this._map.off("mousemove", this._onMouseMove);
    }
    this._container.remove();
    this._map = undefined;
  }

  private _onMouseMove = (e: maplibregl.MapMouseEvent) => {
    const { lng, lat } = e.lngLat.wrap();
    const elev = this._map?.queryTerrainElevation(e.lngLat);
    const elevText = elev != null ? `, Elev: ${Math.round(elev)}m` : "";
    this._label.textContent = `Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}${elevText}`;
  };
}
