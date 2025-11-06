// LayerOpacityToggleControl.ts
import maplibregl from "maplibre-gl";

export class LayerToggleControl implements maplibregl.IControl {
  private map!: maplibregl.Map;
  private container!: HTMLDivElement;
  private button!: HTMLButtonElement;

  private readonly layerId: string;
  private readonly hiddenOpacity: number;
  private readonly label: string;

  private isHidden = false;
  private originalOpacity: number | null = null;
  private originalTransition: { duration?: number; delay?: number } | null =
    null;

  constructor(options: {
    layerId: string;
    hiddenOpacity?: number; // small > 0 keeps it queryable
    label?: string;
  }) {
    this.layerId = options.layerId;
    this.hiddenOpacity = options.hiddenOpacity ?? 0.0001;
    this.label = options.label ?? "Layer";
  }

  onAdd(map: maplibregl.Map) {
    this.map = map;

    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";

    this.button = document.createElement("button");
    this.button.type = "button";
    this.button.ariaLabel = `Toggle ${this.label} visibility`;
    this.button.textContent = `Hide ${this.label}`;
    this.button.onclick = () => this.toggle();

    this.container.appendChild(this.button);

    this.captureOriginals();
    this.map.on("styledata", this.handleStyleData);

    return this.container;
  }

  onRemove() {
    this.map.off("styledata", this.handleStyleData);
    if (this.container.parentNode)
      this.container.parentNode.removeChild(this.container);
    // @ts-expect-error cleanup
    this.map = undefined;
  }

  private handleStyleData = () => {
    if (!this.map.getLayer(this.layerId)) return;
    if (this.isHidden) {
      this.applyNoTransition();
      this.safeSetOpacity(this.hiddenOpacity);
    } else {
      this.captureOriginals();
    }
  };

  private captureOriginals() {
    if (!this.map.getLayer(this.layerId)) return;
    const curr = this.map.getPaintProperty(this.layerId, "fill-opacity");
    this.originalOpacity = (curr as number) ?? 1;

    const t = this.map.getPaintProperty(
      this.layerId,
      "fill-opacity-transition",
    );
    this.originalTransition = (t as { duration?: number; delay?: number }) ?? {
      duration: 300,
      delay: 0,
    };
  }

  private applyNoTransition() {
    try {
      this.map.setPaintProperty(this.layerId, "fill-opacity-transition", {
        duration: 0,
        delay: 0,
      });
    } catch {
      /* ignore */
    }
  }

  private restoreTransition() {
    if (!this.originalTransition) return;
    try {
      this.map.setPaintProperty(
        this.layerId,
        "fill-opacity-transition",
        this.originalTransition,
      );
    } catch {
      /* ignore */
    }
  }

  private toggle() {
    if (!this.map.getLayer(this.layerId)) {
      console.warn(`Layer not found: ${this.layerId}`);
      return;
    }

    // Make the change immediate
    this.applyNoTransition();

    if (this.isHidden) {
      // Show
      if (this.originalOpacity == null) this.captureOriginals();
      if (this.originalOpacity != null) {
        this.safeSetOpacity(this.originalOpacity);
      }
      this.isHidden = false;
      this.button.textContent = `Hide ${this.label}`;
    } else {
      // Hide (but keep queryable)
      this.captureOriginals();
      this.safeSetOpacity(this.hiddenOpacity);
      this.isHidden = true;
      this.button.textContent = `Show ${this.label}`;
    }

    // Force a repaint so it takes effect without user interaction
    this.map.triggerRepaint();

    // Optional: restore whatever transition the layer had
    // (do it on the next frame to avoid reintroducing delay)
    requestAnimationFrame(() => this.restoreTransition());
  }

  private safeSetOpacity(value: number) {
    try {
      this.map.setPaintProperty(this.layerId, "fill-opacity", value);
    } catch (e) {
      console.error("Failed to set fill-opacity:", e);
    }
  }
}
