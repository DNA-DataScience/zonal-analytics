import maplibregl from "maplibre-gl";

type PointProperties = Record<string, unknown>;

function displayValue(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }
  return String(value);
}

function formatCommissionDate(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  const parsed = new Date(String(value));
  if (Number.isNaN(parsed.getTime())) {
    return "Not available";
  }

  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(
    parsed,
  );
}

function formatCapacity(value: unknown): string {
  if (value === null || value === undefined || value === "") {
    return "Not available";
  }

  const numeric = Number(value);
  if (Number.isNaN(numeric)) {
    return String(value);
  }

  return numeric.toLocaleString(undefined, {
    minimumFractionDigits: 0,
    maximumFractionDigits: 3,
  });
}

function addField(container: HTMLElement, label: string, value: string): void {
  const row = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = `${label}: `;
  row.append(strong, document.createTextNode(value));
  container.append(row);
}

function createTooltipContainer(title: string): HTMLElement {
  const root = document.createElement("div");
  root.style.color = "#111827";
  root.style.fontSize = "13px";
  root.style.lineHeight = "1.45";

  const heading = document.createElement("div");
  heading.textContent = title;
  heading.style.fontWeight = "700";
  heading.style.marginBottom = "6px";
  heading.style.color = "#030712";
  root.append(heading);

  return root;
}

function getFeatureLngLat(
  feature: maplibregl.MapGeoJSONFeature,
): maplibregl.LngLatLike | null {
  const geometry = feature.geometry;
  if (geometry.type !== "Point" || !Array.isArray(geometry.coordinates)) {
    return null;
  }

  const [lng, lat] = geometry.coordinates;
  if (typeof lng !== "number" || typeof lat !== "number") {
    return null;
  }

  return [lng, lat];
}

function buildCmsTooltip(properties: PointProperties): HTMLElement {
  const root = createTooltipContainer("CMS Station");
  addField(root, "State / Site Office", displayValue(properties.site_office));
  return root;
}

function buildWtgTooltip(properties: PointProperties): HTMLElement {
  const root = createTooltipContainer("WTG Site");
  addField(root, "Customer", displayValue(properties.customer_name));
  addField(root, "Main site", displayValue(properties.main_site));
  addField(root, "Commissioned", formatCommissionDate(properties.comm_date));
  addField(root, "Installed capacity", formatCapacity(properties.inst_capacity));
  return root;
}

export function attachPointHoverTooltip(map: maplibregl.Map): () => void {
  const popup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
    className: "point-hover-popup",
    offset: 10,
  });

  const clear = () => {
    map.getCanvas().style.cursor = "";
    popup.remove();
  };

  const onMove = (event: maplibregl.MapMouseEvent) => {
    const features = map.queryRenderedFeatures(event.point, {
      layers: ["cms-stations", "wtg-sites"],
    });

    if (features.length === 0) {
      clear();
      return;
    }

    const feature = features[0];
    const lngLat = getFeatureLngLat(feature);
    if (!lngLat) {
      clear();
      return;
    }

    const properties = (feature.properties ?? {}) as PointProperties;
    const content =
      feature.layer.id === "cms-stations"
        ? buildCmsTooltip(properties)
        : buildWtgTooltip(properties);

    map.getCanvas().style.cursor = "pointer";
    popup.setLngLat(lngLat).setDOMContent(content).addTo(map);
  };

  const onLeave = () => {
    clear();
  };

  map.on("mousemove", onMove);
  map.on("mouseleave", onLeave);

  return () => {
    map.off("mousemove", onMove);
    map.off("mouseleave", onLeave);
    clear();
  };
}
