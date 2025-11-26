import maplibregl from "maplibre-gl";
import { MaplibreTerradrawControl } from "@watergis/maplibre-gl-terradraw";

export class CalibrationMenuControl implements maplibregl.IControl {
  private map!: maplibregl.Map;
  private container!: HTMLDivElement;
  private menuButton!: HTMLButtonElement;
  private menuPanel!: HTMLDivElement;
  private calibrateButton!: HTMLButtonElement;
  private draw: MaplibreTerradrawControl | null = null;
  private isExpanded: boolean = false;

  onAdd(map: maplibregl.Map): HTMLElement {
    this.map = map;

    // Main container
    this.container = document.createElement("div");
    this.container.className = "maplibregl-ctrl maplibregl-ctrl-group";
    this.container.style.position = "relative";

    // Menu toggle button
    this.menuButton = document.createElement("button");
    this.menuButton.type = "button";
    this.menuButton.textContent = "✏️"; // Drawing icon
    this.menuButton.title = "Runway Calibration Tools";
    this.menuButton.className = "maplibregl-ctrl-icon";
    this.menuButton.style.cssText = `
  width: 32px;
  height: 32px;
  border: none;
  background-color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  border-radius: 4px 4px 0 0;
`;
    // 1. Update the menu button click handler
    this.menuButton.onclick = (e) => {
      e.stopPropagation();
      this.toggleMenu();
    };

    // Menu panel
    this.menuPanel = document.createElement("div");
    this.menuPanel.style.cssText = `
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 1px;
  background: #fff;
  border: 1px solid #ccc;
  border-radius: 0 0 4px 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  display: none;
  flex-direction: column;
  overflow: hidden;
  z-index: 1000;
`;

    // Apply button (don't add to panel here - it will be added in openMenu)
    this.calibrateButton = document.createElement("button");
    this.calibrateButton.type = "button";
    this.calibrateButton.textContent = "Apply Calibration";
    this.calibrateButton.style.cssText = `
  padding: 8px;
  font-size: 11px;
  border: none;
  background-color: #007cbf;
  color: white;
  border-radius: 0;
  cursor: pointer;
  font-weight: 500;
  white-space: nowrap;
  text-align: center;
  width: 100%;
  box-sizing: border-box;
`;
    this.calibrateButton.onclick = () => this.sendRunway();

    // Add hover effects
    this.addHoverEffects(this.menuButton, "#f0f0f0", "#fff");
    this.addHoverEffects(this.calibrateButton, "#005a87", "#007cbf");

    // Assemble the control (don't add calibrateButton here)
    this.container.appendChild(this.menuButton);
    this.container.appendChild(this.menuPanel);

    // Replace the entire click-outside logic with this more targeted approach:

    // 2. Add click prevention to the menu panel
    this.menuPanel.addEventListener("click", (e) => {
      e.stopPropagation();
    });

    // 3. Close menu only on Escape key or explicit close
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && this.isExpanded) {
        this.closeMenu();
      }
    });

    // 4. Optional: Close when clicking specifically on the map background
    // Remove the broad document listener entirely and use map-specific events
    // This will be added after the map is available in openMenu()

    return this.container;
  }

  onRemove() {
    this.cleanup();
    if (this.container.parentNode) {
      this.container.parentNode.removeChild(this.container);
    }
    // @ts-expect-error cleanup
    this.map = undefined;
  }

  private toggleMenu() {
    if (this.isExpanded) {
      this.closeMenu();
    } else {
      this.openMenu();
    }
  }

  // Update the openMenu method to add map-specific close behavior:
  private openMenu() {
    if (this.isExpanded) return;

    this.isExpanded = true;

    // Update button styling for expanded state
    this.menuButton.style.backgroundColor = "#f0f0f0";
    this.menuButton.style.borderRadius = "4px 4px 0 0";
    this.menuButton.style.borderBottom = "1px solid #ccc";

    // Create and add draw control
    this.draw = new MaplibreTerradrawControl({
      modes: [
        "angled-rectangle",
        "select",
        "delete-selection",
        "delete",
        "download",
      ],
      open: true,
    });

    // Get the draw control element and style it
    const drawElement = this.draw.onAdd(this.map);
    drawElement.style.cssText = `
    margin: 0;
    box-shadow: none;
    border: none;
    border-bottom: 1px solid #eee;
    border-radius: 0;
    background: #fafafa;
  `;

    // Prevent draw control from closing the menu
    drawElement.addEventListener("click", (e) => {
      e.stopPropagation();
    });

    // Add elements to panel
    this.menuPanel.appendChild(drawElement);
    this.menuPanel.appendChild(this.calibrateButton);

    // Show menu panel
    this.menuPanel.style.display = "flex";

    // Add map-specific close behavior (only close on double-click on map)
    const mapCloseHandler = (e: {
      originalEvent: { target: HTMLElement; detail: number };
    }) => {
      const target = e.originalEvent?.target as HTMLElement;
      if (target?.classList.contains("maplibregl-canvas")) {
        // Only close on double-click to avoid interfering with drawing
        if (e.originalEvent?.detail === 2) {
          this.closeMenu();
          this.map.off("click", mapCloseHandler);
        }
      }
    };

    // Use a timeout to avoid immediate closing
    setTimeout(() => {
      this.map.on("click", mapCloseHandler);
    }, 100);
  }

  // Update the closeMenu method:
  private closeMenu() {
    if (!this.isExpanded) return;

    this.isExpanded = false;

    // Reset button styling
    this.menuButton.style.backgroundColor = "#fff";
    this.menuButton.style.borderRadius = "4px";
    this.menuButton.style.borderBottom = "none";

    this.menuPanel.style.display = "none";

    // Clean up draw control
    if (this.draw) {
      try {
        this.draw.onRemove();
      } catch (e) {
        console.warn("Error removing draw control:", e);
      }
      this.draw = null;
    }

    // Clear menu panel contents
    while (this.menuPanel.firstChild) {
      this.menuPanel.removeChild(this.menuPanel.firstChild);
    }
  }

  private cleanup() {
    if (this.draw) {
      try {
        this.draw.onRemove();
      } catch (e) {
        console.warn("Error cleaning up draw control:", e);
      }
      this.draw = null;
    }
  }

  private addHoverEffects(
    button: HTMLButtonElement,
    hoverColor: string,
    normalColor: string,
  ) {
    button.onmouseenter = () => {
      if (!this.isExpanded || button !== this.menuButton) {
        button.style.backgroundColor = hoverColor;
      }
    };
    button.onmouseleave = () => {
      if (!this.isExpanded || button !== this.menuButton) {
        button.style.backgroundColor = normalColor;
      }
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

      if (!this.draw) {
        this.showToast("Drawing tools are not active", "error");
        return;
      }

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

      // Optionally close the menu after successful submission
      this.closeMenu();
    } catch (error) {
      // Reset button state in case of error
      this.calibrateButton.textContent = "Apply Calibration";
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
