// New API type definitions
export type CombinedZone = {
  layer: "combined";
  zone: "Combined Analysis";
  feasibility: "No" | "NOC" | "Yes";
  min_height: string;
  note: string;
  contributing_restrictions: string[];
  total_airport_zones: number;
  total_mod_zones: number;
  total_forest_zones?: number;
};

export type AirportZone = {
  layer: "airport";
  zone: "funnel" | "inner" | "middle" | "outer";
  name: string;
  type: string;
  radio: "VFR" | "IFR";
  feasibility: "No" | "NOC" | "Yes";
  min_height: string;
  note: string;
  distance?: number;
  airport_elevation: number;
  cczm: string;
  autoSettle: "Yes" | "No" | "N/A";
};

export type ModZone = {
  layer: "mod";
  zone:
    | "NO_WTG"
    | "NOC"
    | "NO_NOC"
    | "SPECIAL_ALLOWED"
    | "SPECIAL_LIMITED_HEIGHT";
  name: string;
  type: string;
  feasibility: "No" | "NOC" | "Yes";
  min_height: string;
  note: string;
};

export type ForestZone = {
  layer: "forest";
  zone?: string;
  name: string;
};

export type ReportZone = CombinedZone | AirportZone | ModZone | ForestZone;

// Legacy type for backwards compatibility
export type BackendZone = {
  airport_elevation: string;
  feasibility: string;
  min_height: string;
  name: string;
  note: string;
  radio: string;
  type: string;
  zone: string;
  distance?: number | string;
  cczm: string;
  autoSettle: string;
};

function renderCczmButton(cczm: string): string {
  if (cczm.toLowerCase() === "na") {
    return `<span style="color: #666; font-style: italic;">Not Available for this Airport</span>`;
  }

  const pdfUrl = `https://nocas.aai.aero/nocas/CCZMPDF_Links/CCZMMap_${cczm}.pdf`;
  return `<a href="${pdfUrl}" target="_blank" rel="noopener noreferrer" style="
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: #007bff;
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: background-color 0.2s;
  " onmouseover="this.style.backgroundColor='#0056b3'" onmouseout="this.style.backgroundColor='#007bff'">
    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" />
    </svg>
    View CCZM Map
  </a>`;
}

// Helper: Render feasibility badge with appropriate color
function renderFeasibilityBadge(feasibility: string): string {
  const badges = {
    No: '<span class="badge badge-no">Not Feasible</span>',
    NOC: '<span class="badge badge-noc">NOC Required</span>',
    Yes: '<span class="badge badge-yes">Feasible</span>',
    Unknown: '<span class="badge badge-unknown">Unknown</span>',
  };
  return badges[feasibility as keyof typeof badges] || badges["Unknown"];
}

// Helper: Render zone count badges
function renderZoneCountBadges(
  airportCount: number,
  modCount: number,
  forestCount?: number,
): string {
  const forestBadge =
    forestCount !== undefined
      ? `<span class="count-badge count-forest">${forestCount} Forest Zone${forestCount !== 1 ? "s" : ""}</span>`
      : "";
  return `
    <div class="zone-counts">
      <span class="count-badge count-airport">${airportCount} Airport Zone${airportCount !== 1 ? "s" : ""}</span>
      <span class="count-badge count-mod">${modCount} MoD Zone${modCount !== 1 ? "s" : ""}</span>
      ${forestBadge}
    </div>
  `;
}

// Helper: Render contributing restrictions list
function renderContributingRestrictions(restrictions: string[]): string {
  if (!restrictions || restrictions.length === 0) {
    return '<p class="no-restrictions">No specific restrictions identified.</p>';
  }

  const items = restrictions
    .map((r) => {
      const isAirport = r.toLowerCase().includes("airport:");
      const isMod = r.toLowerCase().includes("mod:");
      const dotColor = isAirport ? "#ef4444" : isMod ? "#f59e0b" : "#94a3b8";
      return `<li><span class="restriction-dot" style="color: ${dotColor};">●</span> ${r}</li>`;
    })
    .join("");

  return `<ul class="contributing-restrictions">${items}</ul>`;
}

// Helper: Render airport zone card
function renderAirportZoneCard(
  zone: AirportZone,
  isNearest: boolean = false,
): string {
  const distanceText = zone.distance ? `${Math.round(zone.distance)}m` : "N/A";
  const elevationText = `${zone.airport_elevation}m`;
  const zoneLabel =
    zone.zone.charAt(0).toUpperCase() + zone.zone.slice(1) + " Zone";
  const autoSettleBadge =
    zone.autoSettle === "Yes"
      ? '<span class="badge badge-yes badge-small">Auto-Settle: Yes</span>'
      : `<span class="auto-settle">Auto-Settle: ${zone.autoSettle}</span>`;

  return `
    <div class="zone-card airport-card">
      <div class="zone-card-header">
        <h4 class="zone-card-title">${zone.name}</h4>
        ${isNearest ? '<span class="nearest-label">Nearest Airport (Reference)</span>' : ""}
      </div>
      <div class="zone-card-body">
        <div class="zone-field">
          <span class="field-label">Feasibility:</span>
          ${renderFeasibilityBadge(zone.feasibility)}
        </div>
        <div class="zone-field">
          <span class="field-label">Zone Type:</span>
          <span class="field-value">${zoneLabel}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">Airport Type:</span>
          <span class="field-value">${zone.type}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">Radio:</span>
          <span class="field-value">${zone.radio}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">Elevation:</span>
          <span class="field-value">${elevationText}</span>
        </div>
        ${
          zone.distance
            ? `<div class="zone-field">
          <span class="field-label">Distance:</span>
          <span class="field-value">${distanceText}</span>
        </div>`
            : ""
        }
        <div class="zone-field">
          <span class="field-label">Min Height:</span>
          <span class="field-value">${zone.min_height}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">${autoSettleBadge}</span>
        </div>
        <div class="zone-field zone-note">
          <span class="field-label">Note:</span>
          <span class="field-value">${zone.note}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">CCZM Map:</span>
          <div class="field-value">${renderCczmButton(zone.cczm)}</div>
        </div>
      </div>
    </div>
  `;
}

// Helper: Render MoD zone card
function renderModZoneCard(zone: ModZone): string {
  const zoneTypeLabels: Record<string, string> = {
    NO_WTG: "No WTG Allowed",
    NOC: "NOC Required",
    NO_NOC: "No NOC Required",
    SPECIAL_ALLOWED: "Special Permission Allowed",
    SPECIAL_LIMITED_HEIGHT: "Special Limited Height",
  };
  const zoneLabel = zoneTypeLabels[zone.zone] || zone.zone;

  return `
    <div class="zone-card mod-card">
      <div class="zone-card-header">
        <h4 class="zone-card-title">${zone.name}</h4>
      </div>
      <div class="zone-card-body">
        <div class="zone-field">
          <span class="field-label">Feasibility:</span>
          ${renderFeasibilityBadge(zone.feasibility)}
        </div>
        <div class="zone-field">
          <span class="field-label">Zone Classification:</span>
          <span class="field-value">${zoneLabel}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">Type:</span>
          <span class="field-value">${zone.type}</span>
        </div>
        <div class="zone-field">
          <span class="field-label">Min Height:</span>
          <span class="field-value">${zone.min_height}</span>
        </div>
        <div class="zone-field zone-note">
          <span class="field-label">Note:</span>
          <span class="field-value">${zone.note}</span>
        </div>
      </div>
    </div>
  `;
}

function renderForestZoneCard(zone: ForestZone): string {
  return `
    <div class="zone-card forest-card">
      <div class="zone-card-header">
        <h4 class="zone-card-title">${zone.name}</h4>
      </div>
    </div>
  `;
}

export function renderZonesFromJson(
  items: ReportZone[] | BackendZone[] | undefined | null,
): string {
  // Normalize input to array
  const list: (ReportZone | BackendZone)[] = Array.isArray(items)
    ? items
    : items
      ? (Object.values(items) as unknown as (ReportZone | BackendZone)[])
      : [];

  if (!list || list.length === 0) {
    return `
      <div class="report-section combined-section">
        <div class="combined-header">
          <h3>Feasibility Analysis</h3>
          ${renderFeasibilityBadge("Unknown")}
        </div>
        <p class="combined-note">No data available for this location. Unable to determine feasibility.</p>
      </div>
    `;
  }

  // Check if this is new API format (has 'layer' field)
  const isNewFormat = list.some((item) => "layer" in item);

  if (!isNewFormat) {
    // Legacy format - fallback to old rendering logic
    return renderLegacyFormat(list as BackendZone[]);
  }

  // New API format
  const zones = list as ReportZone[];

  // Extract combined analysis (first item with layer="combined")
  const combinedIndex = zones.findIndex((z) => z.layer === "combined");
  const combined: CombinedZone | undefined =
    combinedIndex >= 0 ? (zones[combinedIndex] as CombinedZone) : undefined;

  // Extract airport and mod zones
  const airportZones: AirportZone[] = zones.filter(
    (z) => z.layer === "airport",
  ) as AirportZone[];
  const modZones: ModZone[] = zones.filter(
    (z) => z.layer === "mod",
  ) as ModZone[];
  const forestZones: ForestZone[] = zones.filter(
    (z) => z.layer === "forest",
  ) as ForestZone[];
  const forestCount = combined?.total_forest_zones ?? forestZones.length;

  let html = "";

  // Render Combined Analysis Section
  if (combined) {
    html += `
      <div class="report-section combined-section">
        <div class="combined-header">
          <h3>Feasibility Analysis</h3>
          ${renderFeasibilityBadge(combined.feasibility)}
        </div>
        <p class="combined-note">${combined.note}</p>
        ${
          combined.contributing_restrictions &&
          combined.contributing_restrictions.length > 0
            ? `
          <div class="restrictions-section">
            <h4>Contributing Restrictions:</h4>
            ${renderContributingRestrictions(combined.contributing_restrictions)}
          </div>
        `
            : ""
        }
        ${renderZoneCountBadges(combined.total_airport_zones, combined.total_mod_zones, forestCount)}
        <div class="zone-field">
          <span class="field-label">Maximum Allowed Height:</span>
          <span class="field-value">${combined.min_height}</span>
        </div>
      </div>
    `;
  } else if (airportZones.length > 0) {
    // No combined analysis, but have airport zones - use autoSettle logic
    const nearestAirport = airportZones[0];
    const feasibility = nearestAirport.autoSettle === "Yes" ? "Yes" : "Unknown";
    const note =
      nearestAirport.autoSettle === "Yes"
        ? "Location is feasible based on nearest airport auto-settlement policy."
        : "Feasibility status could not be determined. Please review nearest airport information.";

    html += `
      <div class="report-section combined-section">
        <div class="combined-header">
          <h3>Feasibility Analysis</h3>
          ${renderFeasibilityBadge(feasibility)}
        </div>
        <p class="combined-note">${note}</p>
        ${renderZoneCountBadges(airportZones.length, modZones.length, forestZones.length)}
      </div>
    `;
  }

  // Render Airport Zones Section
  if (airportZones.length > 0) {
    const isExpanded = airportZones.length <= 3;
    const airportCards = airportZones
      .map((zone) => {
        const isNearest = zone.distance !== undefined && zone.distance > 0;
        return renderAirportZoneCard(zone, isNearest);
      })
      .join("");

    html += `
      <div class="report-section zone-section">
        <details class="zone-details" ${isExpanded ? "open" : ""}>
          <summary class="section-header">
            <span class="section-title">Airport Zones</span>
            <span class="section-count">${airportZones.length}</span>
          </summary>
          <div class="zone-cards">
            ${airportCards}
          </div>
        </details>
      </div>
    `;
  } else if (combined && combined.total_airport_zones === 0) {
    html += `
      <div class="report-section zone-section">
        <div class="section-header">
          <span class="section-title">Airport Zones</span>
          <span class="section-count">0</span>
        </div>
        <p class="empty-state">✓ No airport zones found at this location</p>
      </div>
    `;
  }

  // Render MoD Zones Section
  if (modZones.length > 0) {
    const isExpanded = modZones.length <= 3;
    const modCards = modZones.map((zone) => renderModZoneCard(zone)).join("");

    html += `
      <div class="report-section zone-section">
        <details class="zone-details" ${isExpanded ? "open" : ""}>
          <summary class="section-header">
            <span class="section-title">MoD Zones</span>
            <span class="section-count">${modZones.length}</span>
          </summary>
          <div class="zone-cards">
            ${modCards}
          </div>
        </details>
      </div>
    `;
  } else if (combined && combined.total_mod_zones === 0) {
    html += `
      <div class="report-section zone-section">
        <div class="section-header">
          <span class="section-title">MoD Zones</span>
          <span class="section-count">0</span>
        </div>
        <p class="empty-state">✓ No MoD zones found at this location</p>
      </div>
    `;
  }

  // Render Forest Zones Section
  if (forestZones.length > 0) {
    const isExpanded = forestZones.length <= 3;
    const forestCards = forestZones
      .map((zone) => renderForestZoneCard(zone))
      .join("");

    html += `
      <div class="report-section zone-section">
        <details class="zone-details" ${isExpanded ? "open" : ""}>
          <summary class="section-header">
            <span class="section-title">Forest Zones</span>
            <span class="section-count">${forestZones.length}</span>
          </summary>
          <div class="zone-cards">
            ${forestCards}
          </div>
        </details>
      </div>
    `;
  } else if (combined && forestCount === 0) {
    html += `
      <div class="report-section zone-section">
        <div class="section-header">
          <span class="section-title">Forest Zones</span>
          <span class="section-count">0</span>
        </div>
        <p class="empty-state">✓ No forest zones found at this location</p>
      </div>
    `;
  }

  return html;
}

// Legacy format renderer (kept for backwards compatibility)
function renderLegacyFormat(list: BackendZone[]): string {
  const isNearest = (z?: string) => z?.toLowerCase().includes("nearest");
  const nearest = list.find((it) => isNearest(it.zone));

  if (nearest) {
    const distRaw = nearest.distance;
    const distNum =
      typeof distRaw === "string" ? parseFloat(distRaw) : Number(distRaw);
    const distText = Number.isFinite(distNum)
      ? `${Math.round(distNum)}m`
      : `${distRaw ?? "N/A"}`;

    return `
      <div class="report-section combined-section">
        <div class="combined-header">
          <h3>Feasibility Analysis</h3>
          ${renderFeasibilityBadge("Yes")}
        </div>
        <p class="combined-note">No zones intersect this location. Nearest airport information is provided below.</p>
      </div>
      <div class="report-section zone-section">
        <div class="section-header">
          <span class="section-title">Nearest Airport</span>
        </div>
        <div class="zone-card airport-card">
          <div class="zone-card-header">
            <h4 class="zone-card-title">${nearest.name}</h4>
            <span class="nearest-label">Nearest Airport (Reference)</span>
          </div>
          <div class="zone-card-body">
            <div class="zone-field">
              <span class="field-label">Airport Elevation:</span>
              <span class="field-value">${nearest.airport_elevation}m</span>
            </div>
            <div class="zone-field">
              <span class="field-label">Airport Type:</span>
              <span class="field-value">${nearest.type}</span>
            </div>
            <div class="zone-field">
              <span class="field-label">Radio:</span>
              <span class="field-value">${nearest.radio}</span>
            </div>
            <div class="zone-field">
              <span class="field-label">Distance:</span>
              <span class="field-value">${distText}</span>
            </div>
            <div class="zone-field">
              <span class="field-label">Auto Settle:</span>
              <span class="field-value">${nearest.autoSettle}</span>
            </div>
            <div class="zone-field zone-note">
              <span class="field-label">Note:</span>
              <span class="field-value">${nearest.note}</span>
            </div>
            <div class="zone-field">
              <span class="field-label">CCZM Map:</span>
              <div class="field-value">${renderCczmButton(nearest.cczm)}</div>
            </div>
          </div>
        </div>
      </div>
    `;
  }

  // Old multi-zone logic
  let html = '<ul class="rules">';
  let anyNotFeasible = false;
  let anyHeightReq = false;
  let anyNumericHeight = false;
  let minHeight = Number.POSITIVE_INFINITY;

  const toZoneLabel = (raw: string | undefined): string => {
    const v = (raw ?? "").toLowerCase();
    if (v.includes("inner")) return "Inner Zone";
    if (v.includes("middle")) return "Middle Zone";
    if (v.includes("outer")) return "Outer Zone";
    if (v.includes("funnel")) return "Funnel Zone";
    return raw ?? "";
  };

  for (const it of list) {
    const v = (it.feasibility ?? "").toLowerCase();
    if (v.includes("not feasible") || v === "no") anyNotFeasible = true;
    else if (v.includes("height") || v.includes("restricted"))
      anyHeightReq = true;

    const parsedH = parseFloat(it.min_height ?? "");
    if (!Number.isNaN(parsedH)) {
      anyNumericHeight = true;
      if (parsedH < minHeight) minHeight = parsedH;
    }

    html += `
      <li>
        <strong>Airport:</strong> ${it.name}
        <dl class="airport-info">
          <dt><strong>Airport Elevation:</strong></dt><dd>${it.airport_elevation}m</dd>
          <dt><strong>Airport Type:</strong></dt><dd>${it.type}</dd>
          <dt><strong>Radio Type:</strong></dt><dd>${it.radio}</dd>
          <dt><strong>Zone:</strong></dt><dd>${toZoneLabel(it.zone)}</dd>
          <dt><strong>Note:</strong></dt><dd>${it.note}</dd>
          <dt><strong>CCZM Map:</strong></dt><dd>${renderCczmButton(it.cczm)}</dd>
        </dl>
      </li>
    `;
  }

  html += "</ul></div>";

  if (anyNotFeasible) {
    html += `<div><strong>Maximum Allowed Windmill Height:</strong> Restricted</div>`;
  } else if (anyNumericHeight) {
    html += `<div><strong>Maximum Allowed Windmill Height:</strong> ${Math.round(minHeight)}m</div>`;
  } else if (anyHeightReq) {
    html += `<div><strong>Maximum Allowed Windmill Height:</strong> Height Restriction Applies</div>`;
  } else {
    html += `<div><strong>Maximum Allowed Windmill Height:</strong> No Restrictions</div>`;
  }

  if (anyNotFeasible)
    html += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: red">No</span></div>`;
  else if (anyHeightReq || anyNumericHeight)
    html += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: orange">Yes with Height Requirements</span></div>`;
  else
    html += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: lawngreen">Yes</span></div>`;

  return html;
}
