import json
import csv
from datetime import datetime
import os
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException

# Import feasibility analysis functions from centralized module
from feasibility_engine import (
    find_most_restrictive_airport_zone,
    find_most_restrictive_mod_zone,
    find_most_restrictive_forest_zone,
    determine_feasibility,
    format_zone_description
)


async def get_batch_airport_zones(coordinates: List[Dict], db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Query airport_layers for all coordinates in a single optimized batch query.
    """
    points_json = json.dumps(coordinates)
    
    query = text("""
        WITH points AS (
          SELECT
            (p->>'id')::int AS pid,
            ST_Transform(
              ST_SetSRID(
                ST_MakePoint(
                  (p->>'lon')::float,
                  (p->>'lat')::float
                ),
                4326
              ),
              3857
            ) AS geom
          FROM jsonb_array_elements(CAST(:points AS jsonb)) AS p
        )
        SELECT
          p.pid,
          z.zone,
          z.name,
          z.type,
          z.radio,
          z.elevation
        FROM points p
        JOIN "GisDB".airport_layers z
          ON z.geom3857 && p.geom
         AND ST_Intersects(z.geom3857, p.geom)
    """)
    
    result = await db.execute(query, {"points": points_json})
    rows = result.fetchall()
    print(rows)
    
    results = []
    for row in rows:
        results.append({
            "pid": row[0],
            "zone": row[1],
            "name": row[2],
            "type": row[3],
            "radio": row[4],
            "elevation": row[5]
        })
    
    return results


async def get_batch_mod_zones(coordinates: List[Dict], db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Query mod_layers for all coordinates in a single optimized batch query.
    """
    points_json = json.dumps(coordinates)
    
    query = text("""
        WITH points AS (
          SELECT
            (p->>'id')::int AS pid,
            ST_Transform(
              ST_SetSRID(
                ST_MakePoint(
                  (p->>'lon')::float,
                  (p->>'lat')::float
                ),
                4326
              ),
              3857
            ) AS geom
          FROM jsonb_array_elements(CAST(:points AS jsonb)) AS p
        )
        SELECT
          p.pid,
          z.zone,
          z.name,
          z.type
        FROM points p
        JOIN "GisDB".mod_layers z
          ON z.geom3857 && p.geom
        AND ST_Intersects(z.geom3857, p.geom)
    """)
    
    result = await db.execute(query, {"points": points_json})
    rows = result.fetchall()
    
    print(rows)
    
    results = []
    for row in rows:
        results.append({
            "pid": row[0],
            "zone": row[1],
            "name": row[2],
            "type": row[3]
        })
    
    return results


async def get_batch_forest_zones(coordinates: List[Dict], db: AsyncSession) -> List[Dict[str, Any]]:
        """
        Query reserve_forests for all coordinates in a single optimized batch query.
        """
        points_json = json.dumps(coordinates)

        query = text("""
                WITH points AS (
                    SELECT
                        (p->>'id')::int AS pid,
                        ST_Transform(
                            ST_SetSRID(
                                ST_MakePoint(
                                    (p->>'lon')::float,
                                    (p->>'lat')::float
                                ),
                                4326
                            ),
                            3857
                        ) AS geom
                    FROM jsonb_array_elements(CAST(:points AS jsonb)) AS p
                )
                SELECT
                    p.pid,
                    z."Name"
                FROM points p
                JOIN "GisDB".reserve_forests z
                    ON z.geom3857 && p.geom
                 AND ST_Intersects(z.geom3857, p.geom)
        """)

        result = await db.execute(query, {"points": points_json})
        rows = result.fetchall()

        results = []
        for row in rows:
                results.append({
                        "pid": row[0],
                        "zone": "inner",
                        "name": row[1] or "Unknown Forest",
                        "type": "forest"
                })

        return results


def save_batch_to_csv(
    coordinates: List[Dict],
    feasibility_results: List[Dict]
) -> Tuple[str, str]:
    """
    Generate batch processing results with feasibility analysis as CSV in-memory.
    
    Creates a CSV with one row per coordinate, including:
    - Latitude, Longitude
    - Feasibility (Yes/NOC/No)
    - Most Restrictive Airport Zone
    - Most Restrictive MoD Zone
    
    Args:
        coordinates: List of dicts with format [{"id": 1, "lat": x, "lon": y}, ...]
        feasibility_results: List of dicts with feasibility analysis per coordinate
        
    Returns:
        Tuple of (CSV content string, timestamp string)
        
    Raises:
        ValueError: If data validation fails
    """
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create a lookup dict for coordinates by pid for faster access
    coords_lookup = {coord.get("id"): coord for coord in coordinates}
    
    # Generate CSV in-memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    header = [
        'Latitude',
        'Longitude',
        'Feasibility',
        'Most Restrictive Airport Zone',
        'Most Restrictive MoD Zone',
        'Most Restrictive Forest Zone'
    ]
    writer.writerow(header)
    
    # Write each coordinate with feasibility analysis
    for result in feasibility_results:
        pid = result.get("pid")
        coord = coords_lookup.get(pid, {})
        
        row = [
            coord.get("lat", ""),  # Latitude
            coord.get("lon", ""),  # Longitude
            result.get("feasibility", ""),  # Feasibility (Yes/NOC/No)
            result.get("most_restrictive_airport", "No zones exist"),  # Airport Zone
            result.get("most_restrictive_mod", "No zones exist"),  # MoD Zone
            result.get("most_restrictive_forest", "No zones exist")  # Forest Zone
        ]
        writer.writerow(row)
    
    csv_content = output.getvalue()
    output.close()
    
    return csv_content, timestamp


async def generate_batch_report(coordinates: List[Dict], db: AsyncSession) -> Dict[str, Any]:
    """
    Main function for batch coordinate processing with feasibility analysis.
    
    Executes both airport and MoD zone queries, determines feasibility for each
    coordinate, exports results to CSV, and returns summary.
    
    Args:
        coordinates: List of dicts with format [{"id": 1, "lat": x, "lon": y}, ...]
        db: AsyncSession from database connection
        
    Returns:
        Dictionary with:
        - feasibility_results: List of results per coordinate
        - summary_counts: Counts by feasibility/color
        - csv_file: Output CSV filename
        
    Raises:
        HTTPException: If batch size exceeds limits or database errors occur
    """
    # Validate batch size
    if len(coordinates) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 coordinates per batch request")
    if len(coordinates) == 0:
        raise HTTPException(status_code=400, detail="At least 1 coordinate required")
    
    try:
        # Execute both batch queries
        airport_zones = await get_batch_airport_zones(coordinates, db)
        mod_zones = await get_batch_mod_zones(coordinates, db)
        forest_zones = await get_batch_forest_zones(coordinates, db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")
    
    # Group zones by coordinate ID
    airport_zones_by_pid = {}
    for zone in airport_zones:
        pid = zone.get("pid")
        if pid not in airport_zones_by_pid:
            airport_zones_by_pid[pid] = []
        airport_zones_by_pid[pid].append(zone)
    
    mod_zones_by_pid = {}
    for zone in mod_zones:
        pid = zone.get("pid")
        if pid not in mod_zones_by_pid:
            mod_zones_by_pid[pid] = []
        mod_zones_by_pid[pid].append(zone)

    forest_zones_by_pid = {}
    for zone in forest_zones:
        pid = zone.get("pid")
        if pid not in forest_zones_by_pid:
            forest_zones_by_pid[pid] = []
        forest_zones_by_pid[pid].append(zone)
    
    # Perform feasibility analysis for each coordinate
    feasibility_results = []
    summary_counts = {"green": 0, "yellow": 0, "red": 0}
    
    for coord in coordinates:
        pid = coord.get("id")
        
        # Find most restrictive zones for this coordinate
        airport_zone_type, airport_zone_dict = find_most_restrictive_airport_zone(
            airport_zones_by_pid.get(pid, [])
        )
        mod_zone_type, mod_zone_dict = find_most_restrictive_mod_zone(
            mod_zones_by_pid.get(pid, [])
        )
        forest_zone_type, forest_zone_dict = find_most_restrictive_forest_zone(
            forest_zones_by_pid.get(pid, [])
        )
        
        # Determine feasibility based on zone combination
        feasibility, color = determine_feasibility(airport_zone_type, mod_zone_type, forest_zone_type)
        
        # Format zone descriptions
        airport_desc = format_zone_description(airport_zone_type, airport_zone_dict, "airport")
        mod_desc = format_zone_description(mod_zone_type, mod_zone_dict, "mod")
        forest_desc = format_zone_description(forest_zone_type, forest_zone_dict, "forest")
        
        # Store result
        result = {
            "pid": pid,
            "feasibility": feasibility,
            "color": color,
            "most_restrictive_airport": airport_desc,
            "most_restrictive_mod": mod_desc,
            "most_restrictive_forest": forest_desc
        }
        feasibility_results.append(result)
        summary_counts[color] += 1
    
    # Generate CSV in memory
    try:
        csv_content, timestamp = save_batch_to_csv(coordinates, feasibility_results)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")
    
    # Return CSV content for streaming
    return {
        "csv_content": csv_content,
        "timestamp": timestamp
    }
