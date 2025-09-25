"use client";
import React, {useEffect, useRef} from 'react';
import maplibregl, { Map as MapType } from 'maplibre-gl'
//import 'maplibre-gl/dist/maplibre-gl.css';
import MaplibreGeocoder, {
    CarmenGeojsonFeature,
    MaplibreGeocoderApiConfig,
    MaplibreGeocoderFeatureResults
} from '@maplibre/maplibre-gl-geocoder';

const geo = {
    // required
    forwardGeocode: async (config: MaplibreGeocoderApiConfig) => {
        const features: MaplibreGeocoderFeatureResults = {
            type: "FeatureCollection",
            features: []
        }
        // const features = []
        try {
            // More info about the Nominatim API: https://nominatim.org/release-docs/develop/api/Search/
            // Please respect their usage policy: https://operations.osmfoundation.org/policies/nominatim/
            const request =
            `https://nominatim.openstreetmap.org/search?q=${
                config.query
            }&format=geojson&polygon_geojson=1&addressdetails=1`;
            const response = await fetch(request);
            const geojson = await response.json();
            for (const feature of geojson.features) {
                const center = [
                    feature.bbox[0] +
                (feature.bbox[2] - feature.bbox[0]) / 2,
                    feature.bbox[1] +
                (feature.bbox[3] - feature.bbox[1]) / 2
                ];
                const point: CarmenGeojsonFeature = {
                    id: "",
                    type: 'Feature',
                    geometry: {
                        type: 'Point',
                        coordinates: center,
                    },
                    place_name: feature.properties.display_name,
                    properties: feature.properties,
                    text: feature.properties.display_name,
                    place_type: ['place']
                    //center: center
                };
                features.features.push(point);
                // features.push(point);
            }
        } catch (e) {
            console.error(`Failed to forwardGeocode with error: ${e}`); 
        }
        return features;
        // return {
        //     features
        // };
    },
    // optional
    // reverseGeocode: async (config) => { /* definition here */ }, // reverse geocoding API
    // getSuggestions: async (config) => { /* definition here */ }, // suggestion API
    // searchByPlaceId: async (config) => { /* definition here */ } // search by Place ID API
};

const Map: React.FC = () => {
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<MapType | null>(null);

    useEffect(() => {
        if (mapRef.current || !mapContainerRef.current) return; // initialize only once

        const map = new maplibregl.Map({
            container: mapContainerRef.current,
            // You can get a free key from https://www.maptiler.com/
            // I recommend storing it in an environment variable.
            style: `https://tiles.openfreemap.org/styles/bright`,
            center: [78.9629, 20.5937], // India center [lng, lat]
            zoom: 4,
            pitch: 45,
            bearing: -17.6,
        });
        mapRef.current = map;

        map.on('load', () => {
            if (!mapRef.current) return;

            map.addControl(new maplibregl.NavigationControl(), 'top-right');

            map.addControl(new MaplibreGeocoder(geo, {
                maplibregl,
            }), 'top-left');

            const layers = map.getStyle().layers;
            let labelLayerId = '';
            for (const layer of layers) {
                if (layer.type === 'symbol' && layer.layout && layer.layout['text-field']) {
                    labelLayerId = layer.id;
                    break;
                }
            }

            // Add state boundaries
            map.addLayer({
                id: 'state-boundaries',
                type: 'line',
                source: 'openmaptiles',
                'source-layer': 'boundary',
                filter: ['==', 'admin_level', 4],
                paint: {
                    'line-color': '#4A5568', // A shade of gray
                    'line-width': 1.5,
                    'line-dasharray': [2, 1],
                }
            }, labelLayerId);

            // Helper to safely add a layer before labels
            // const addBelowLabels = (layer: maplibregl.LayerSpecification) => {
            //     if (labelLayerId) {
            //         map.addLayer(layer, labelLayerId);
            //     } else {
            //         map.addLayer(layer);
            //     }
            // };

            // Forests (from landuse, class=forest)
            map.addLayer({
                id: 'landuse-forest-fill',
                type: 'fill',
                source: 'openmaptiles',
                'source-layer': 'landcover',
                filter: ['==', ['get', 'class'], 'wood'],
                paint: {
                    'fill-color': '#1fcc31',
                    'fill-opacity': 1.0,
                    'fill-outline-color': '#000000',
                },
            });

            // Military areas (from landuse, class=military)
            map.addLayer({
                id: 'landuse-military-fill',
                type: 'fill',
                source: 'openmaptiles',
                'source-layer': 'landuse',
                filter: ['==', ['get', 'class'], 'military'],
                paint: {
                    'fill-color': '#e74c3c',
                    'fill-opacity': 1.0,
                    'fill-outline-color': '#000000',
                },
            });



        });

        return () => {
            if (mapRef.current) {
                mapRef.current.remove();
                mapRef.current = null;
            }
        };
    }, []);

    return <div ref={mapContainerRef} style={{width: '100vw', height: '100vh'}} />;

}

export default Map;