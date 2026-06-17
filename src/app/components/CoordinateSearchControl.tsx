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

    // Visual styling for this control lives in src/app/ui-theme.css
    // (.coordinate-search-ctrl), keeping the design centralized.

    this._container.innerHTML = `
      <div style="display: flex; flex-direction: column; gap: 6px; padding: 8px;">
        <input id="latInput" type="number" step="any" placeholder="Latitude (-90 to 90)" style="width: 150px; padding: 6px 8px;" />
        <input id="lngInput" type="number" step="any" placeholder="Longitude (-180 to 180)" style="width: 150px; padding: 6px 8px;" />
        <button id="flyBtn" style="padding: 6px 8px;">Go</button>
        <div id="errorMsg" style="color: #dc2626; font-size: 12px; min-height: 14px; font-weight: 500;"></div>
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

      if (
        lat < 6.747139 ||
        lat > 35.495405 ||
        lng < 68.17665 ||
        lng > 97.40256
      ) {
        if (errorMsg) {
          errorMsg.textContent = "Enter Coords within India Bounds";
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
