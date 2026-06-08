from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
import math

# Import feasibility analysis functions from centralized module
from feasibility_engine import (
    find_most_restrictive_airport_zone,
    find_most_restrictive_mod_zone,
    find_most_restrictive_forest_zone,
    determine_feasibility,
    build_airport_zone_report,
    build_mod_zone_report,
    build_forest_zone_report,
    build_combined_analysis,
    calculate_autosettle
)

REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation, z."CCZM_Cities",
                           ST_Distance(
                               p.geom4326::geography,
                               z.airport_point::geography
                            ) AS distance_m
                    FROM "GisDB".airport_layers z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);                  
                    """)

NEAREST_QUERY = text("""
                     WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation, z."CCZM_Cities",
                           ST_Distance(
                               p.geom4326::geography,
                               z.airport_point::geography
                            ) AS distance_m
                    FROM "GisDB".airport_layers z
                    CROSS JOIN p
                    ORDER BY
                        z.geom3857 <-> p.geom3857
                    LIMIT 1;    
                     """)

MOD_REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type
                    FROM "GisDB".mod_layers z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);                  
                    """)

FOREST_REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z."Name"
                    FROM "GisDB".reserve_forests z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);
                    """)

async def generate_report(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    
    # Fetch airport zones
    try:
        result = await db.execute(REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        airport_rows = result.fetchall()
    except Exception as e:
        print(f"Error retrieving airport zone data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    # Fetch MoD zones
    try:
        result = await db.execute(MOD_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        mod_rows = result.fetchall()
    except Exception as e:
        print(f"Error retrieving MoD zone data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch forest zones
    try:
        result = await db.execute(FOREST_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        forest_rows = result.fetchall()
    except Exception as e:
        print(f"Error retrieving forest zone data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    report = []
    
    # Convert database rows to zone dictionaries
    airport_zones = []
    for r in airport_rows:
        airport_zones.append({
            "zone": r[0],
            "name": r[1],
            "type": r[2],
            "radio": r[3],
            "elevation": r[4],
            "CCZM_Cities": r[5],
            "distance": float(r[6])
        })
    
    mod_zones = []
    for r in mod_rows:
        mod_zones.append({
            "zone": r[0],
            "name": r[1],
            "type": r[2]
        })

    forest_zones = []
    for r in forest_rows:
        forest_zones.append({
            "zone": "inner",
            "name": r[0] or "Unknown Forest",
            "type": "forest"
        })
    
    # Build individual airport zone reports
    airport_reports = []
    for zone_dict in airport_zones:
        airport_report = build_airport_zone_report(zone_dict, zone_dict["distance"], elev)
        airport_reports.append(airport_report)
    
    # Build individual MoD zone reports
    mod_reports = []
    for zone_dict in mod_zones:
        mod_report = build_mod_zone_report(zone_dict)
        mod_reports.append(mod_report)

    # Build individual forest zone reports
    forest_reports = []
    for zone_dict in forest_zones:
        forest_report = build_forest_zone_report(zone_dict)
        forest_reports.append(forest_report)
    
    # If no airport zones found, get nearest airport for auto-settlement info
    nearest_airport_data = None
    if not airport_zones and not mod_zones and not forest_zones:
        nearest_airport_data = await get_nearest_airport_data(lat, lng, elev, db)
    
    # If we have neither airport zones nor mod zones nor nearest airport, return error
    if not airport_reports and not mod_reports and not forest_reports and not nearest_airport_data:
        return JSONResponse(content={"status": "no_results", "message": "No zones or airports found"})
    
    # Create combined analysis if we have zone intersections
    if airport_reports or mod_reports or forest_reports:
        # Find most restrictive zones
        airport_zone_type, airport_zone_dict = find_most_restrictive_airport_zone(airport_zones)
        mod_zone_type, mod_zone_dict = find_most_restrictive_mod_zone(mod_zones)
        forest_zone_type, forest_zone_dict = find_most_restrictive_forest_zone(forest_zones)
        
        # Build combined analysis
        combined = build_combined_analysis(
            airport_reports,
            mod_reports,
            (airport_zone_type, airport_zone_dict) if airport_zone_type else None,
            (mod_zone_type, mod_zone_dict) if mod_zone_type else None,
            elev,
            forest_reports,
            (forest_zone_type, forest_zone_dict) if forest_zone_type else None
        )
        report.append(combined)
    
    # Add all individual airport zones
    report.extend(airport_reports)
    
    # Add all individual MoD zones
    report.extend(mod_reports)

    # Add all individual forest zones
    report.extend(forest_reports)
    
    # Add nearest airport data if no airport zones were found
    if nearest_airport_data:
        report.append(nearest_airport_data)
    
    return JSONResponse(content=report)


async def get_nearest_airport_data(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    """Get nearest airport data for auto-settlement info"""
    try:
        result = await db.execute(NEAREST_QUERY, {
            "lat": lat,
            "lon": lng
        })
        
        row = result.fetchall()
        
        if not row:
            return None
        
    except Exception as e:
        print(f"Error retrieving nearest airport: {str(e)}")
        return None
    
    r = row[0]
    zone = "nearest"
    name = r[1]
    air_type = r[2]
    radio = r[3]
    air_elev = r[4]
    distance_m = float(r[6])
    feasibility = "Feasible"
    note = "Auto Settle only viable if height of WTG is 150m or less"
    min_height = "Not Required"
    crz = "na" if r[5] is None else r[5]
    
    # Use centralized autoSettle calculation
    autoSettle = calculate_autosettle(radio, distance_m)
    
    return {
        "layer": "airport",
        "zone": zone,
        "name": name,
        "type": air_type,
        "radio": radio,
        "airport_elevation": air_elev,
        "min_height": min_height,
        "note": note,
        "feasibility": feasibility,
        "distance": distance_m,
        "cczm": crz,
        "autoSettle": autoSettle
    }