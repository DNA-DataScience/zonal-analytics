// Backend-driven renderer
export type BackendZone = {
  airport_elevation: string; // e.g. "4.9"
  feasibility: string; // e.g. "Feasible", "Not Feasible", "Yes with Height Requirements"
  min_height: string; // e.g. "Not Required" or a numeric string like "120"
  name: string; // airport name
  note: string; // descriptive note
  radio: string; // e.g. "VFR"
  type: string; // e.g. "AAI / Joint Venture"
  zone: string; // e.g. "inner" | "middle" | "outer" | "funnel"
  distance?: number | string; // meters, present only for `nearest`;
};

export function renderZonesFromJson(
  items: BackendZone[] | undefined | null,
): string {
  let rules: string = `<ul class="rules">`;

  const list: BackendZone[] = Array.isArray(items)
    ? items
    : items
      ? (Object.values(items) as unknown as BackendZone[])
      : [];

  const isNearest = (z?: string) => z?.toLowerCase().includes("nearest");
  const nearest = list.find((it) => isNearest(it.zone));

  if (nearest) {
    let nearestBlock = "";
    const distRaw = (nearest as BackendZone).distance;
    const distNum =
      typeof distRaw === "string" ? parseFloat(distRaw) : Number(distRaw);
    const distText = Number.isFinite(distNum)
      ? `${Math.round(distNum)}m`
      : `${distRaw ?? "N/A"}`;

    nearestBlock = `
        
        <div><strong>Nearest Airport:</strong></div>
        <div class="nearest-airport">
          <dl class="airport-info">
            <dt><strong>Airport:</strong></dt><dd>${nearest.name}</dd>
            <dt><strong>Airport Elevation:</strong></dt><dd>${nearest.airport_elevation}${/m$/i.test(String(nearest.airport_elevation)) ? "" : "m"}</dd>
            <dt><strong>Airport Type:</strong></dt><dd>${nearest.type}</dd>
            <dt><strong>Radio Type:</strong></dt><dd>${nearest.radio}</dd>
            <dt><strong>Distance:</strong></dt><dd>${distText}</dd>
          </dl>
        </div>`;

    return (
      rules +
      `<li>
          No Zones
        </li>` +
      `</ul>` +
      `</div>` +
      nearestBlock +
      `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: lawngreen">Yes</span></div>`
    );
  }

  // if (!list.length) {
  //   return (
  //     rules +
  //     `<li>
  //         No Zones
  //       </li>` +
  //     `</ul>` +
  //     `</div>` +
  //     `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: lawngreen">Yes</span></div></div>`
  //   );
  // }

  // Aggregation flags based on backend-provided semantics
  let anyNotFeasible = false;
  let anyHeightReq = false;
  let anyFeasible = false;

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

  const classifyFeas = (txt?: string) => {
    const v = (txt ?? "").toLowerCase();
    if (!v) return;
    if (v.includes("not feasible") || v === "no") anyNotFeasible = true;
    else if (v.includes("height") || v.includes("restricted"))
      anyHeightReq = true;
    else if (v.includes("feasible") || v === "yes") anyFeasible = true;
  };

  for (const it of list) {
    const zoneLabel = toZoneLabel(it.zone);

    classifyFeas(it.feasibility);

    const parsedH = parseFloat((it.min_height as unknown as string) ?? "");
    if (!Number.isNaN(parsedH)) {
      anyNumericHeight = true;
      if (parsedH < minHeight) minHeight = parsedH;
    }

    rules += `
      <li>
        <strong>Airport:</strong> ${it.name}
        <dl class="airport-info">
          <dt><strong>Airport Elevation:</strong></dt><dd>${it.airport_elevation}${/m$/i.test(String(it.airport_elevation)) ? "" : "m"}</dd>
          <dt><strong>Airport Type:</strong></dt><dd>${it.type}</dd>
          <dt><strong>Radio Type:</strong></dt><dd>${it.radio}</dd>
          <dt><strong>Zone:</strong></dt><dd>${zoneLabel}</dd>
          <dt><strong>Note:</strong></dt><dd>${it.note}</dd>
        </dl>
      </li>
    `;
  }

  rules += `</ul>
            </div>`;

  // Height summary prefers backend semantics
  if (anyNotFeasible) {
    rules += `<div><strong>Maximum Allowed Windmill Height:</strong> Restricted</div>`;
  } else if (anyNumericHeight) {
    rules += `<div><strong>Maximum Allowed Windmill Height:</strong> ${Math.round(minHeight)}m</div>`;
  } else if (anyHeightReq) {
    rules += `<div><strong>Maximum Allowed Windmill Height:</strong> Height Restriction Applies</div>`;
  } else {
    rules += `<div><strong>Maximum Allowed Windmill Height:</strong> No Restrictions</div>`;
  }

  // Overall feasibility prefers backend field
  if (anyNotFeasible)
    rules += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: red">No</span></div>`;
  else if (anyHeightReq || anyNumericHeight)
    rules += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: orange">Yes with Height Requirements</span></div>`;
  else
    rules += `<div style="font-weight: bold; font-size: 20px;"><strong>Feasibility: </strong><span style="color: lawngreen">Yes</span></div>`;

  return rules;
}
