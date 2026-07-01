import { IControl, Map as MapType } from "maplibre-gl";
import { addLayers } from "@/app/lib/Layerer";

type StyleId = "liberty" | "bright";

export class StyleToggleControl implements IControl {
  private _container!: HTMLElement;
  private _button!: HTMLButtonElement;
  private _map?: MapType;
  private _index: number;

  private readonly _styles: Array<{ id: StyleId; url: string; label: string }> =
    [
      {
        id: "liberty",
        url: "https://tiles.openfreemap.org/styles/liberty",
        label: "Liberty",
      },
      {
        id: "bright",
        url: "https://tiles.openfreemap.org/styles/bright",
        label: "Bright",
      },
    ];

  constructor(initial: StyleId = "bright") {
    const i = this._styles.findIndex((s) => s.id === initial);
    this._index = i >= 0 ? i : 0;
  }

  onAdd(map: MapType): HTMLElement {
    this._map = map;

    const container = document.createElement("div");
    container.className = "maplibregl-ctrl maplibregl-ctrl-group";

    const button = document.createElement("button");
    button.type = "button";
    button.title = "Switch base map";
    button.setAttribute("aria-label", "Switch base map");
    button.textContent = "🗺️";
    button.addEventListener("click", () => this.toggle());

    container.appendChild(button);

    this._container = container;
    this._button = button;
    return container;
  }

  onRemove(): void {
    this._container.remove();
    this._map = undefined;
  }

  private toggle(): void {
    const map = this._map;
    if (!map) return;

    this._index = (this._index + 1) % this._styles.length;
    const next = this._styles[this._index];

    map.setStyle(next.url);

    // Re-apply DEM terrain and any custom layers/sources after the new style loads
    map.once("style.load", () => {
      addLayers(map);
    });
  }
}
