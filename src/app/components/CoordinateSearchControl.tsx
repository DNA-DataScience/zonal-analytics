import maplibregl from "maplibre-gl";
import { ContextMenuControl } from "@/app/components/ContextMenuControl";

export class CoordinateSearchControl implements maplibregl.IControl {
  private _container!: HTMLDivElement;
  private _map?: maplibregl.Map;
  private _control: ContextMenuControl;
  private _styleEl?: HTMLStyleElement;

  constructor(control: ContextMenuControl) {
    this._control = control;
  }

  onAdd(map: maplibregl.Map): HTMLElement {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl coordinate-search-ctrl";

    if (!document.getElementById("coordinate-search-ctrl-style")) {
      const style = document.createElement("style");
      style.id = "coordinate-search-ctrl-style";
      style.textContent = `
        .maplibregl-ctrl.coordinate-search-ctrl {
          background: white;
          border-radius: 6px;
          box-shadow: 0 1px 3px rgba(0,0,0,0.3);
          font-family: sans-serif;
        }
        .maplibregl-ctrl.coordinate-search-ctrl input {
          border: 1px solid #ccc;
          border-radius: 4px;
          color: black;
        }
        .maplibregl-ctrl.coordinate-search-ctrl button {
          background: #0078ff;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
        }
        .maplibregl-ctrl.coordinate-search-ctrl button:hover {
          background: #005ec2;
        }
      `;
      document.head.appendChild(style);
      this._styleEl = style;
    }

    this._container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 4px; padding: 6px;">
        <input id="latInput" type="number" step="any" placeholder="Latitude (-90 to 90)" style="width: 140px; padding: 4px;" />
        <input id="lngInput" type="number" step="any" placeholder="Longitude (-180 to 180)" style="width: 140px; padding: 4px;" />
        <button id="flyBtn" style="padding: 4px;">Go</button>
        <div id="errorMsg" style="color: red; font-size: 12px; min-height: 14px;"></div>
      </div>
    `;

    const latInput =
      this._container.querySelector<HTMLInputElement>("#latInput");
    const lngInput =
      this._container.querySelector<HTMLInputElement>("#lngInput");
    const flyBtn = this._container.querySelector<HTMLButtonElement>("#flyBtn");
    const errorMsg = this._container.querySelector<HTMLDivElement>("#errorMsg");

    const goToLocation = () => {
      if (!latInput || !lngInput) {
        if (errorMsg) {
          errorMsg.textContent = "Please Fill Both Inputs";
          return;
        }
      }

      const lat = parseFloat(latInput?.value as string);
      const lng = parseFloat(lngInput?.value as string);

      if (Number.isNaN(lat) || Number.isNaN(lng)) {
        if (errorMsg) {
          errorMsg.textContent = "Please Enter Valid Numbers";
          return;
        }
      }

      if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
        if (errorMsg) {
          errorMsg.textContent =
            "Latitude must be between -90 and 90, longitude between -180 and 180.";
        }
        return;
      }

      if (errorMsg) {
        errorMsg.textContent = "";
      }

      if (this._map) {
        this._map.flyTo({
          center: [lng, lat],
          zoom: 12,
        });
      }

      this._control.showAt([lng, lat]);
    };

    flyBtn?.addEventListener("click", goToLocation);

    [latInput, lngInput].forEach((input) => {
      input?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          goToLocation();
        }
      });
    });

    return this._container;
  }

  onRemove() {
    if (this._styleEl) {
      this._styleEl.remove();
      this._styleEl = undefined;
    }
    this._container.remove();
    this._map = undefined;
  }
}
