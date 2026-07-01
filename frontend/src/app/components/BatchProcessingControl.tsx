import maplibregl from "maplibre-gl";
import { trackEvent } from "@/app/lib/analytics";
import { showToast } from "@/app/lib/toast";

interface Coordinate {
  id: number;
  lat: number;
  lon: number;
}

export class BatchProcessingControl implements maplibregl.IControl {
  private _container!: HTMLDivElement;
  private _panel!: HTMLDivElement;
  private _map?: maplibregl.Map;
  private _styleEl?: HTMLStyleElement;
  private _isOpen = false;
  private _mode: "table" | "paste" = "table";
  private _coordinates: Coordinate[] = [];
  private _nextId = 1;

  onAdd(map: maplibregl.Map): HTMLElement {
    this._map = map;
    this._container = document.createElement("div");
    this._container.className = "maplibregl-ctrl batch-processing-tab";

    // Add styles
    if (!document.getElementById("batch-processing-style")) {
      const style = document.createElement("style");
      style.id = "batch-processing-style";
      style.textContent = `
        .maplibregl-ctrl.batch-processing-tab {
          position: relative;
          z-index: 3;
        }

        .batch-processing-panel {
          position: fixed;
          right: 12px;
          top: 12px;
          width: 380px;
          display: none;
          flex-direction: column;
          max-height: calc(100vh - 24px);
          overflow: hidden;
          z-index: 101;
        }

        .batch-processing-panel.open {
          display: flex;
        }

        .batch-processing-body {
          flex: 1 1 auto;
          overflow-y: auto;
          padding: 12px 14px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .batch-processing-mode-toggle {
          display: flex;
          gap: 8px;
          border-bottom: 1px solid #e2e8f0;
          padding-bottom: 12px;
        }

        .batch-processing-mode-btn {
          flex: 1;
          padding: 8px 12px;
          border: 1px solid #e2e8f0;
          background: #f8fafc;
          color: #64748b;
          border-radius: 6px;
          cursor: pointer;
          font: 500 12px/1.2 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
          transition: all 0.15s ease;
        }

        .batch-processing-mode-btn.active {
          background-color: var(--ui-accent) !important;
          color: #ffffff;
          border-color: var(--ui-accent);
        }

        .batch-processing-mode-btn:hover:not(.active) {
          background-color: #e2e8f0 !important;
          border-color: #cbd5e1;
        }

        .batch-processing-table {
          width: 100%;
          border-collapse: collapse;
          font: 400 12px/1.4 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
          margin-bottom: 12px;
        }

        .batch-processing-table thead {
          background: #f1f5f9;
          border-bottom: 1px solid #e2e8f0;
        }

        .batch-processing-table th {
          padding: 8px 6px;
          text-align: left;
          font-weight: 600;
          color: #0f172a;
          border: none;
        }

        .batch-processing-table td {
          padding: 8px 6px;
          border-bottom: 1px solid #e2e8f0;
        }

        .batch-processing-table input {
          width: 100%;
          padding: 6px 4px;
          border: 1px solid #cbd5e1;
          border-radius: 4px;
          font: 400 12px/1 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
          color: #0f172a;
        }

        .batch-processing-table input:focus {
          outline: none;
          border-color: var(--ui-accent);
          box-shadow: 0 0 0 3px var(--ui-accent-ring);
          background: #ffffff;
        }

        .batch-processing-table input.error {
          border-color: #dc2626;
          background: #fee;
        }

        .batch-processing-table-actions {
          display: flex;
          gap: 4px;
          justify-content: center;
        }

        .batch-processing-table-btn {
          appearance: none;
          background: #f1f5f9;
          border: 1px solid #cbd5e1;
          color: #0f172a;
          border-radius: 4px;
          width: 24px;
          height: 24px;
          cursor: pointer;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font: 600 12px/1;
          transition: all 0.15s ease;
        }

        .batch-processing-table-btn:hover {
          background-color: #e2e8f0 !important;
          border-color: #94a3b8;
        }

        .batch-processing-table-btn.remove:hover {
          background-color: #fee2e2 !important;
          border-color: #fca5a5;
          color: #dc2626;
        }

        .batch-processing-paste-area {
          width: 100%;
          padding: 8px;
          border: 1px solid #cbd5e1;
          border-radius: 6px;
          font: 400 12px/1.4 "Courier New", monospace;
          color: #0f172a;
          resize: vertical;
          min-height: 150px;
          font-family: "Courier New", monospace;
        }

        .batch-processing-paste-area:focus {
          outline: none;
          border-color: var(--ui-accent);
          box-shadow: 0 0 0 3px var(--ui-accent-ring);
          background: #ffffff;
        }

        .batch-processing-paste-area.error {
          border-color: #dc2626;
          background: #fee;
        }

        .batch-processing-paste-hint {
          font-size: 11px;
          color: #64748b;
          line-height: 1.4;
          margin: 8px 0;
          padding: 8px;
          background: #f1f5f9;
          border-radius: 4px;
          border-left: 2px solid #cbd5e1;
        }

        .batch-processing-error-message {
          font-size: 11px;
          color: #dc2626;
          margin-top: 4px;
          padding: 6px 8px;
          background: #fee;
          border-radius: 4px;
          border-left: 2px solid #fca5a5;
        }

        .batch-processing-counter {
          font-size: 12px;
          color: #64748b;
          text-align: center;
          padding: 8px;
          background: #f1f5f9;
          border-radius: 4px;
          margin: 8px 0;
        }

        .batch-processing-footer {
          display: flex;
          gap: 8px;
          padding: 12px 14px;
          border-top: 1px solid #e2e8f0;
          background: #f8fafc;
        }

        .batch-processing-btn {
          flex: 1;
          padding: 8px 12px;
          border: none;
          border-radius: 6px;
          font: 500 12px/1.2 system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans", "Liberation Sans";
          cursor: pointer;
          transition: all 0.15s ease;
        }

        .batch-processing-btn-primary {
          background-color: var(--ui-accent) !important;
          color: #ffffff;
        }

        .batch-processing-btn-primary:hover {
          background-color: var(--ui-accent-hover) !important;
        }

        .batch-processing-btn-secondary {
          background-color: #f1f5f9 !important;
          color: #0f172a;
          border: 1px solid #cbd5e1;
        }

        .batch-processing-btn-secondary:hover {
          background-color: #e2e8f0 !important;
          border-color: #94a3b8;
        }

        .batch-processing-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `;
      document.head.appendChild(style);
      this._styleEl = style;
    }

    // Create tab button
    const tabButton = document.createElement("button");
    tabButton.className = "batch-processing-tab-button";
    tabButton.textContent = "Batch";
    tabButton.title = "Batch Processing";
    tabButton.addEventListener("click", () => this.toggle());

    // Create panel
    this._panel = document.createElement("div");
    this._panel.className = "batch-processing-panel";
    this._panel.innerHTML = `
      <div class="batch-processing-header">
        <div class="batch-processing-title">Batch Processing</div>
        <button class="batch-processing-close" aria-label="Close">×</button>
      </div>
      <div class="batch-processing-body">
        <div class="batch-processing-mode-toggle">
          <button class="batch-processing-mode-btn active" data-mode="table">Table</button>
          <button class="batch-processing-mode-btn" data-mode="paste">Paste</button>
        </div>
        
        <!-- Table Mode -->
        <div class="batch-processing-mode-content" data-mode="table">
          <div class="batch-processing-counter"><span id="table-counter">0</span>/100 coordinates</div>
          <div style="overflow-y: auto; flex: 1;">
            <table class="batch-processing-table">
              <thead>
                <tr>
                  <th style="width: 25%;">ID</th>
                  <th style="width: 37.5%;">Latitude</th>
                  <th style="width: 37.5%;">Longitude</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody id="table-body"></tbody>
            </table>
          </div>
          <button class="batch-processing-btn batch-processing-btn-secondary" id="add-row-btn">+ Add Row</button>
        </div>

        <!-- Paste Mode -->
        <div class="batch-processing-mode-content" data-mode="paste" style="display: none;">
          <div class="batch-processing-paste-hint">
            Format: <strong>lat,lon;lat,lon;lat,lon</strong><br>
            Example: 20.43,76.12;19.07,72.87;18.52,73.86
          </div>
          <textarea class="batch-processing-paste-area" id="paste-area" placeholder="Paste coordinates here..."></textarea>
          <div id="paste-error" class="batch-processing-error-message" style="display: none;"></div>
          <div class="batch-processing-counter">Detected: <span id="paste-counter">0</span> coordinates</div>
        </div>
      </div>
      <div class="batch-processing-footer">
        <button class="batch-processing-btn batch-processing-btn-secondary" id="clear-btn">Clear</button>
        <button class="batch-processing-btn batch-processing-btn-primary" id="generate-btn">Generate</button>
      </div>
    `;

    this._container.appendChild(tabButton);
    this._container.appendChild(this._panel);

    // Attach event listeners
    this._attachEventListeners();

    return this._container;
  }

  private _attachEventListeners() {
    const closeBtn = this._panel.querySelector(
      ".batch-processing-close",
    ) as HTMLButtonElement;
    closeBtn?.addEventListener("click", () => this.close());

    // Mode toggle buttons
    const modeButtons = this._panel.querySelectorAll(
      ".batch-processing-mode-btn",
    ) as NodeListOf<HTMLButtonElement>;
    modeButtons.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const mode = (e.target as HTMLElement).getAttribute("data-mode") as
          | "table"
          | "paste";
        this._switchMode(mode);
      });
    });

    // Table mode buttons
    const addRowBtn = this._panel.querySelector(
      "#add-row-btn",
    ) as HTMLButtonElement;
    addRowBtn?.addEventListener("click", () => this._addTableRow());

    // Paste area
    const pasteArea = this._panel.querySelector(
      "#paste-area",
    ) as HTMLTextAreaElement;
    pasteArea?.addEventListener("input", () => this._validatePasteInput());

    // Clear button
    const clearBtn = this._panel.querySelector(
      "#clear-btn",
    ) as HTMLButtonElement;
    clearBtn?.addEventListener("click", () => this._clearAll());

    // Generate button
    const generateBtn = this._panel.querySelector(
      "#generate-btn",
    ) as HTMLButtonElement;
    generateBtn?.addEventListener("click", () => this._generateReport());
  }

  private _switchMode(mode: "table" | "paste") {
    this._mode = mode;

    // Update button states
    const modeButtons = this._panel.querySelectorAll(
      ".batch-processing-mode-btn",
    ) as NodeListOf<HTMLButtonElement>;
    modeButtons.forEach((btn) => {
      if (btn.getAttribute("data-mode") === mode) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });

    // Update content visibility
    const contents = this._panel.querySelectorAll(
      ".batch-processing-mode-content",
    ) as NodeListOf<HTMLElement>;
    contents.forEach((content) => {
      if (content.getAttribute("data-mode") === mode) {
        content.style.display = "";
      } else {
        content.style.display = "none";
      }
    });

    // Parse data from current mode
    if (mode === "paste") {
      this._validatePasteInput();
    } else {
      this._updateTableCounter();
    }
  }

  private _addTableRow() {
    if (this._coordinates.length >= 100) {
      showToast("Maximum 100 coordinates allowed", "warning");
      return;
    }

    const tbody = this._panel.querySelector(
      "#table-body",
    ) as HTMLTableSectionElement;
    const id = this._nextId++;
    const rowIndex = this._coordinates.length;

    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${id}</td>
      <td><input type="number" class="lat-input" data-index="${rowIndex}" placeholder="-90 to 90" step="0.00001" min="-90" max="90"></td>
      <td><input type="number" class="lon-input" data-index="${rowIndex}" placeholder="-180 to 180" step="0.00001" min="-180" max="180"></td>
      <td class="batch-processing-table-actions">
        <button class="batch-processing-table-btn remove" data-index="${rowIndex}" title="Remove row">−</button>
      </td>
    `;

    tbody.appendChild(row);

    // Add input change listeners
    const latInput = row.querySelector(".lat-input") as HTMLInputElement | null;
    const lonInput = row.querySelector(".lon-input") as HTMLInputElement | null;

    const validateInput = (input: HTMLInputElement) => {
      const val = parseFloat(input.value);
      if (input.value === "") {
        input.classList.remove("error");
      } else if (input.classList.contains("lat-input")) {
        input.classList.toggle("error", isNaN(val) || val < -90 || val > 90);
      } else {
        input.classList.toggle("error", isNaN(val) || val < -180 || val > 180);
      }
      this._updateTableCounter();
    };

    latInput?.addEventListener("input", () => validateInput(latInput));
    lonInput?.addEventListener("input", () => validateInput(lonInput));

    // Remove button
    const removeBtn = row.querySelector(
      ".batch-processing-table-btn.remove",
    ) as HTMLButtonElement | null;
    removeBtn?.addEventListener("click", () => {
      row.remove();
      this._updateTableCounter();
    });

    this._coordinates.push({ id, lat: NaN, lon: NaN });
    this._updateTableCounter();
  }

  private _updateTableCounter() {
    const counter = this._panel.querySelector(
      "#table-counter",
    ) as HTMLElement | null;
    if (counter) {
      const tbody = this._panel.querySelector(
        "#table-body",
      ) as HTMLTableSectionElement;
      counter.textContent = tbody.children.length.toString();
    }
  }

  private _validatePasteInput() {
    const pasteArea = this._panel.querySelector(
      "#paste-area",
    ) as HTMLTextAreaElement;
    const errorDiv = this._panel.querySelector("#paste-error") as HTMLElement;
    const counter = this._panel.querySelector("#paste-counter") as HTMLElement;

    const text = pasteArea.value.trim();
    errorDiv.style.display = "none";

    if (!text) {
      counter.textContent = "0";
      pasteArea.classList.remove("error");
      return;
    }

    const pairs = text.split(";").map((p) => p.trim());
    const results: { valid: Coordinate[]; errors: string[] } = {
      valid: [],
      errors: [],
    };

    pairs.forEach((pair, idx) => {
      if (!pair) return;
      const parts = pair.split(",").map((p) => p.trim());
      if (parts.length !== 2) {
        results.errors.push(`Line ${idx + 1}: Expected format "lat,lon"`);
        return;
      }

      const lat = parseFloat(parts[0]);
      const lon = parseFloat(parts[1]);

      if (isNaN(lat) || isNaN(lon)) {
        results.errors.push(`Line ${idx + 1}: Invalid numbers`);
        return;
      }

      if (lat < -90 || lat > 90) {
        results.errors.push(
          `Line ${idx + 1}: Latitude out of range (-90 to 90)`,
        );
        return;
      }

      if (lon < -180 || lon > 180) {
        results.errors.push(
          `Line ${idx + 1}: Longitude out of range (-180 to 180)`,
        );
        return;
      }

      results.valid.push({ id: results.valid.length + 1, lat, lon });
    });

    this._coordinates = results.valid;
    counter.textContent = results.valid.length.toString();

    if (results.errors.length > 0) {
      pasteArea.classList.add("error");
      errorDiv.style.display = "";
      errorDiv.innerHTML = results.errors
        .map((e) => `<div>${e}</div>`)
        .join("");
    } else {
      pasteArea.classList.remove("error");
    }
  }

  private _collectTableData() {
    const tbody = this._panel.querySelector(
      "#table-body",
    ) as HTMLTableSectionElement;
    const coords: Coordinate[] = [];
    let hasErrors = false;

    tbody.querySelectorAll("tr").forEach((row) => {
      const latInput = row.querySelector(
        ".lat-input",
      ) as HTMLInputElement | null;
      const lonInput = row.querySelector(
        ".lon-input",
      ) as HTMLInputElement | null;

      if (!latInput || !lonInput) return;

      const lat = parseFloat(latInput.value);
      const lon = parseFloat(lonInput.value);

      if (latInput.value === "" || lonInput.value === "") {
        latInput?.classList.add("error");
        lonInput?.classList.add("error");
        hasErrors = true;
        return;
      }

      if (isNaN(lat) || isNaN(lon)) {
        latInput?.classList.add("error");
        lonInput?.classList.add("error");
        hasErrors = true;
        return;
      }

      latInput?.classList.remove("error");
      lonInput?.classList.remove("error");

      const idCell = row.querySelector("td:first-child");
      const id = parseInt(idCell?.textContent || "0", 10);
      coords.push({ id, lat, lon });
    });

    if (hasErrors) {
      showToast("Please fix all coordinate errors before generating", "error");
      return null;
    }

    return coords;
  }

  private _clearAll() {
    if (this._mode === "table") {
      const tbody = this._panel.querySelector(
        "#table-body",
      ) as HTMLTableSectionElement;
      tbody.innerHTML = "";
      this._coordinates = [];
      this._nextId = 1;
      this._updateTableCounter();
    } else {
      const pasteArea = this._panel.querySelector(
        "#paste-area",
      ) as HTMLTextAreaElement;
      pasteArea.value = "";
      this._coordinates = [];
      const errorDiv = this._panel.querySelector("#paste-error") as HTMLElement;
      errorDiv.style.display = "none";
      pasteArea.classList.remove("error");
      this._validatePasteInput();
    }
  }

  private _generateReport() {
    let coords: Coordinate[];

    if (this._mode === "table") {
      const tableCoords = this._collectTableData();
      if (!tableCoords) return;
      coords = tableCoords;
    } else {
      coords = this._coordinates;
    }

    if (!coords || coords.length === 0) {
      showToast("Please enter at least one coordinate", "warning");
      return;
    }

    console.log(JSON.stringify(coords));

    // Send to backend
    this._sendToBackend({ coordinates: coords });
  }

  private async _sendToBackend(coords: { coordinates: Coordinate[] }) {
    try {
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

      trackEvent("batch_submitted", "/batch-generator", {
        count: coords.coordinates.length,
        mode: this._mode,
      });
      trackEvent("api_call", "/batch-generator", {
        count: coords.coordinates.length,
      });

      const response = await fetch(`${apiBaseUrl}/batch-generator`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(coords),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Get the CSV file as a blob
      const blob = await response.blob();

      // Extract filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = "batch_report.csv";

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(
          /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/,
        );
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, "");
        }
      }

      // Create a temporary URL for the blob
      const url = window.URL.createObjectURL(blob);

      // Create a temporary anchor element and trigger download
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      showToast("Batch report downloaded successfully", "success");
    } catch (error) {
      console.error("Error sending batch processing request:", error);
      showToast(
        "Failed to send batch processing request. Please try again.",
        "error",
      );
    }
  }

  toggle() {
    if (this._isOpen) {
      this.close();
    } else {
      this.open();
    }
  }

  open() {
    this._isOpen = true;
    this._container.classList.add("open");
    this._panel.classList.add("open");
  }

  close() {
    this._isOpen = false;
    this._container.classList.remove("open");
    this._panel.classList.remove("open");
  }

  onRemove() {
    this._container?.remove();
    this._map = undefined;
    if (this._styleEl) {
      this._styleEl.remove();
      this._styleEl = undefined;
    }
  }
}
