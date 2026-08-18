from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
import math
import logging

logger = logging.getLogger(__name__)

# Import feasibility analysis functions from centralized module
from app.engine.feasibility_engine import (
    find_most_restrictive_airport_zone,
    find_most_restrictive_mod_zone,
    find_most_restrictive_forest_zone,
    find_most_restrictive_inner_zone,
    determine_feasibility,
    build_airport_zone_report,
    build_mod_zone_report,
    build_forest_zone_report,
    build_inner_zone_report,
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

INNER_ZONES_REPORT_QUERY = text("""
                    WITH p AS (
                       SELECT
                       ST_Transform(
                           ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                           3857
                       ) AS geom3857
                    )
                    SELECT z.category, z."Name", z.state_code, z.state_name
                    FROM "GisDB".inner_zones z
                    JOIN p
                       ON z.geom3857 && p.geom3857
                       AND ST_Intersects(z.geom3857, p.geom3857);
                    """)

async def generate_report(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    logger.info("Generating feasibility report for lat=%s lng=%s elev=%s", lat, lng, elev)

    # Fetch airport zones
    try:
        result = await db.execute(REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        airport_rows = result.fetchall()
        logger.debug("Airport zone query returned %d rows", len(airport_rows))
    except Exception as e:
        logger.exception("Error retrieving airport zone data for lat=%s lng=%s", lat, lng)
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch MoD zones
    try:
        result = await db.execute(MOD_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        mod_rows = result.fetchall()
        logger.debug("MoD zone query returned %d rows", len(mod_rows))
    except Exception as e:
        logger.exception("Error retrieving MoD zone data for lat=%s lng=%s", lat, lng)
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch forest zones
    try:
        result = await db.execute(FOREST_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        forest_rows = result.fetchall()
        logger.debug("Forest zone query returned %d rows", len(forest_rows))
    except Exception as e:
        logger.exception("Error retrieving forest zone data for lat=%s lng=%s", lat, lng)
        raise HTTPException(status_code=500, detail=str(e))

    # Fetch Inner Zones
    try:
        result = await db.execute(INNER_ZONES_REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        inner_zone_rows = result.fetchall()
        logger.debug("Inner Zones query returned %d rows", len(inner_zone_rows))
    except Exception as e:
        logger.exception("Error retrieving Inner Zones data for lat=%s lng=%s", lat, lng)
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

    inner_zones = []
    for r in inner_zone_rows:
        inner_zones.append({
            "zone": r[0],
            "category": r[0],
            "name": r[1] or "Unknown Inner Zone",
            "state_code": r[2],
            "state_name": r[3],
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

    # Build individual Inner Zones reports
    inner_zone_reports = []
    for zone_dict in inner_zones:
        inner_zone_report = build_inner_zone_report(zone_dict)
        inner_zone_reports.append(inner_zone_report)
    
    # If no airport zones found, get nearest airport for auto-settlement info
    nearest_airport_data = None
    if not airport_zones and not mod_zones and not forest_zones and not inner_zones:
        logger.debug("No zone intersections found for lat=%s lng=%s; falling back to nearest airport lookup", lat, lng)
        nearest_airport_data = await get_nearest_airport_data(lat, lng, elev, db)

    # If we have neither airport zones nor mod zones nor nearest airport, return error
    if (
        not airport_reports
        and not mod_reports
        and not forest_reports
        and not inner_zone_reports
        and not nearest_airport_data
    ):
        logger.warning("No zones or airports found for lat=%s lng=%s", lat, lng)
        return JSONResponse(content={"status": "no_results", "message": "No zones or airports found"})

    # Create combined analysis if we have zone intersections
    if airport_reports or mod_reports or forest_reports or inner_zone_reports:
        # Find most restrictive zones
        airport_zone_type, airport_zone_dict = find_most_restrictive_airport_zone(airport_zones)
        mod_zone_type, mod_zone_dict = find_most_restrictive_mod_zone(mod_zones)
        forest_zone_type, forest_zone_dict = find_most_restrictive_forest_zone(forest_zones)
        inner_zone_type, inner_zone_dict = find_most_restrictive_inner_zone(inner_zones)
        logger.debug(
            "Most restrictive zones for lat=%s lng=%s: airport=%s mod=%s forest=%s inner_zones=%s",
            lat, lng, airport_zone_type, mod_zone_type, forest_zone_type, inner_zone_type,
        )

        # Build combined analysis
        combined = build_combined_analysis(
            airport_reports,
            mod_reports,
            (airport_zone_type, airport_zone_dict) if airport_zone_type else None,
            (mod_zone_type, mod_zone_dict) if mod_zone_type else None,
            elev,
            forest_reports,
            (forest_zone_type, forest_zone_dict) if forest_zone_type else None,
            inner_zone_reports,
            (inner_zone_type, inner_zone_dict) if inner_zone_type else None
        )
        logger.info(
            "Combined feasibility for lat=%s lng=%s: %s (min_height=%s)",
            lat, lng, combined.get("feasibility"), combined.get("min_height"),
        )
        report.append(combined)
    
    # Add all individual airport zones
    report.extend(airport_reports)
    
    # Add all individual MoD zones
    report.extend(mod_reports)

    # Add all individual forest zones
    report.extend(forest_reports)

    # Add all individual Inner Zones
    report.extend(inner_zone_reports)
    
    # Add nearest airport data if no airport zones were found
    if nearest_airport_data:
        report.append(nearest_airport_data)

    logger.info("Report generation complete for lat=%s lng=%s: %d section(s)", lat, lng, len(report))
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
            logger.warning("Nearest airport query returned no rows for lat=%s lng=%s", lat, lng)
            return None

    except Exception:
        logger.exception("Error retrieving nearest airport for lat=%s lng=%s", lat, lng)
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
    logger.info(
        "Nearest airport for lat=%s lng=%s: name=%s distance_m=%.1f autoSettle=%s",
        lat, lng, name, distance_m, autoSettle,
    )

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