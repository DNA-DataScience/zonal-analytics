import maplibregl from "maplibre-gl";
import { MaplibreTerradrawControl } from "@watergis/maplibre-gl-terradraw";

export class CalibrationControl implements maplibregl.IControl {
  private map!: maplibregl.Map;
  private container!: HTMLDivElement;
  private calibrateButton!: HTMLButtonElement;
  private draw!: MaplibreTerradrawControl;

  constructor(draw: MaplibreTerradrawControl) {
    this.draw = draw;
  }

  onAdd(map: maplibregl.Map): HTMLElement {
    this.map = map;

    // Main container
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this.container.style.display = "flex";
    this.container.style.flexDirection = "column";
    this.container.style.gap = "2px";

    // Calibrate button (existing functionality)
    this.calibrateButton = document.createElement("button");
    this.calibrateButton.type = "button";
    this.calibrateButton.textContent = "Calibrate";
    this.calibrateButton.className = "maplibregl-ctrl-icon";
    this.calibrateButton.style.padding = "8px 12px";
    this.calibrateButton.style.fontSize = "12px";
    this.calibrateButton.style.border = "none";
    this.calibrateButton.style.backgroundColor = "#fff";
    this.calibrateButton.style.cursor = "pointer";
    this.calibrateButton.onclick = () => this.sendRunway();

    // Add hover effects
    this.addHoverEffects(this.calibrateButton);

    // Append buttons to container
    this.container.appendChild(this.calibrateButton);

    return this.container;
  }

  onRemove() {
    if (this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    // @ts-expect-error cleanup
    this.map = undefined;
  }

  private addHoverEffects(button: HTMLButtonElement) {
    button.onmouseenter = () => {
      button.style.backgroundColor = "#f0f0f0";
    };
    button.onmouseleave = () => {
      button.style.backgroundColor = "#fff";
    };
  }

  private showToast(
    message: string,
    type: "error" | "success" | "info" = "error",
  ) {
    // Create toast container
    const toast = document.createElement("div");
    toast.className = "calibration-toast";
    toast.textContent = message;

    // Base styles
    Object.assign(toast.style, {
      position: "fixed",
      top: "20px",
      right: "20px",
      padding: "12px 16px",
      borderRadius: "4px",
      fontSize: "14px",
      fontWeight: "500",
      color: "#fff",
      zIndex: "10000",
      maxWidth: "300px",
      boxShadow: "0 4px 12px rgba(0, 0, 0, 0.3)",
      opacity: "0",
      transform: "translateX(100%)",
      transition: "all 0.3s ease-in-out",
      cursor: "pointer",
    });

    // Type-specific styles
    const typeStyles = {
      error: { backgroundColor: "#dc3545" },
      success: { backgroundColor: "#28a745" },
      info: { backgroundColor: "#17a2b8" },
    };
    Object.assign(toast.style, typeStyles[type]);

    // Add to DOM
    document.body.appendChild(toast);

    // Animate in
    setTimeout(() => {
      toast.style.opacity = "1";
      toast.style.transform = "translateX(0)";
    }, 100);

    // Auto remove after 4 seconds
    const autoRemoveTimer = setTimeout(() => {
      this.removeToast(toast);
    }, 4000);

    // Click to dismiss
    toast.onclick = () => {
      clearTimeout(autoRemoveTimer);
      this.removeToast(toast);
    };
  }

  private removeToast(toast: HTMLElement) {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
    }, 300);
  }

  private async sendRunway() {
    try {
      console.log("Calibrate action triggered");

      const drawings = this.draw.getFeatures();

      // Check if there are any drawings
      if (!drawings.features || drawings.features.length === 0) {
        this.showToast(
          "No drawings found. Please draw a runway first.",
          "error",
        );
        return;
      }

      const coords = drawings.features[0].geometry.coordinates[0] as [
        number,
        number,
      ][];
      const point = this.map.project(coords[0]);
      const features = this.map.queryRenderedFeatures(point, {
        layers: ["airport-zones"],
      });

      if (features.length === 0) {
        this.showToast("No airport found at this location", "error");
        return;
      }

      const first = features[0];
      if (!first.properties) {
        this.showToast("Airport data is missing", "error");
        return;
      }

      const airportName = first.properties.name;
      console.log(airportName);

      // Show loading state
      const originalText = this.calibrateButton.textContent;
      this.calibrateButton.textContent = "Sending...";
      this.calibrateButton.disabled = true;

      const res = await fetch("http://127.0.0.1:8000/airport/runway-funnel", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          features: drawings.features,
          airportName: airportName,
        }),
      });

      // Reset button state
      this.calibrateButton.textContent = originalText;
      this.calibrateButton.disabled = false;

      if (!res.ok) {
        const errorText = await res.text();
        this.showToast(`Server error: ${res.status} - ${errorText}`, "error");
        return;
      }

      // Success
      this.showToast(
        `Runway calibration sent successfully for ${airportName}`,
        "success",
      );
    } catch (error) {
      // Reset button state in case of error
      this.calibrateButton.textContent = "Calibrate";
      this.calibrateButton.disabled = false;

      if (error instanceof Error) {
        this.showToast(`Network error: ${error.message}`, "error");
      } else {
        this.showToast("An unexpected error occurred", "error");
      }
      console.error("Calibration error:", error);
    }
  }
}
