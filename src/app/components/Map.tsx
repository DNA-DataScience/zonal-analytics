"use client";
import React, {useEffect, useRef} from 'react';
import maplibregl, { Map as MapType } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css';

const Map: React.FC = () => {
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<MapType | null>(null);

    useEffect(() => {
        if (mapRef.current) return; // initialize only once

        if (mapContainerRef.current) {
            mapRef.current = new maplibregl.Map({
                container: mapContainerRef.current,
                style: 'https://tiles.stadiamaps.com/styles/alidade_smooth.json',
                center: [78.9629, 20.5937], // India center [lng, lat]
                zoom: 4,
                pitch: 45,
                bearing: -17.6,
        });

    }

    return () => {
        if (mapRef.current) {
            mapRef.current.remove();
            mapRef.current = null;
        }
    };
    }, []);

    useEffect(() => {
        if (!mapRef.current) return;
        const map = mapRef.current;

        map.on('load', () => {

            map.addControl(new maplibregl.NavigationControl(), 'top-right');


            const layers = map.getStyle().layers;
            let labelLayerId = '';
            for (const layer of layers) {
                if (layer.type === 'symbol' && layer.layout && layer.layout['text-field']) {
                    labelLayerId = layer.id;
                    break;
                }
            }

            map.addLayer(
                {
                    id: '3d-buildings',
                    source: 'openmaptiles',   // Adjust source name as per style
                    'source-layer': 'building',
                    filter: ['==', 'extrude', 'true'],
                    type: 'fill-extrusion',
                    minzoom: 15,
                    paint: {
                    'fill-extrusion-color': '#aaa',
                    'fill-extrusion-height': ['get', 'height'],
                    'fill-extrusion-base': ['get', 'min_height'],
                    'fill-extrusion-opacity': 0.6,
                    },
                },
                labelLayerId
            );
        });

    }, []);

    return <div ref={mapContainerRef} style={{width: '100vw', height: '100vh'}} />;

}

export default Map;