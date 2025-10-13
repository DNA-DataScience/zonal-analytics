import maplibregl from "maplibre-gl";

export class CoordsControl implements maplibregl.IControl {
  private _container!: HTMLDivElement;
  private _label!: HTMLDivElement;
  private _map!: maplibregl.Map;

  onAdd(map: maplibregl.Map) {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this._label = document.createElement("div");
    this._label.style.padding = "6px 8px";
    this._label.style.fontSize = "12px";
    this._label.style.lineHeight = "1";
    this._label.style.backgroundColor = "#fff";
    this._label.style.color = "#000";
    this._label.textContent = "Lng: —, Lat: —";

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

  private _onMouseMove = (
    e: maplibregl.MapMouseEvent & maplibregl.EventData,
  ) => {
    const { lng, lat } = e.lngLat.wrap();
    this._label.textContent = `Lng: ${lng.toFixed(5)}, Lat: ${lat.toFixed(5)}`;
  };
}
