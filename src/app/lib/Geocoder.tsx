import type {
  CarmenGeojsonFeature,
  MaplibreGeocoderApiConfig,
  MaplibreGeocoderFeatureResults,
} from "@maplibre/maplibre-gl-geocoder";

const cacheString = new Map<string, MaplibreGeocoderFeatureResults>();
//const cacheCoords = new Map<number[], MaplibreGeocoderFeatureResults>();

export const geoCoder = {
  forwardGeocode: async (config: MaplibreGeocoderApiConfig) => {
    const features: MaplibreGeocoderFeatureResults = {
      type: "FeatureCollection",
      features: [],
    };

    try {
      if (typeof config.query === "string") {
        const q = config.query.trim();
        if (!q) return features;
        const cached = cacheString.get(q);
        if (cached) return cached;
      }

      // const request =
      //       `https://nominatim.openstreetmap.org/search?` +
      //       `q=${config.query}&format=geojson&polygon_geojson=1&addressdetails=1&limit=10`;

      const request = `https://nominatim.openstreetmap.org/search?q=${
        config.query
      }&format=geojson&addressdetails=0&limit=8&countrycodes=in`;

      const response = await fetch(request); //, {
      //   headers: {
      //     Accept: 'application/geo+json, application/json',
      //     // Replace with your own app info to comply with Nominatim usage policy
      //     'User-Agent': 'map-overlay/0.1.0'
      //   }
      // });
      if (!response.ok) return features;

      const geojson = await response.json();
      for (const feature of geojson.features) {
        const center = [
          feature.bbox[0] + (feature.bbox[2] - feature.bbox[0]) / 2,
          feature.bbox[1] + (feature.bbox[3] - feature.bbox[1]) / 2,
        ];
        const point: CarmenGeojsonFeature = {
          id: "",
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: center,
          },
          place_name: feature.properties.display_name,
          properties: feature.properties,
          text: feature.properties.display_name,
          place_type: ["place"],
          //center: center
        };
        features.features.push(point);
        // features.push(point);
      }
    } catch (e) {
      console.error("Failed to forwardGeocode with error:", e);
    }
    if (typeof config.query === "string") {
      cacheString.set(config.query, features);
    }
    return features;
  },

  // optional
  // reverseGeocode: async (config) => { /* definition here */ }, // reverse geocoding API
  // getSuggestions: async (config) => { /* definition here */ }, // suggestion API
  // searchByPlaceId: async (config) => { /* definition here */ } // search by Place ID API
};
