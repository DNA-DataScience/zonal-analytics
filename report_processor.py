from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse
import math

REPORT_QUERY = text("""
                    WITH p AS (
                        SELECT 
                        ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) AS geom4326,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(:lon, :lat), 4326),
                            3857
                        ) AS geom3857
                    )
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation,
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
                    SELECT z.zone, z.name, z.type, z.radio, z.elevation,
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

async def generate_report(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    
    try:
        result = await db.execute(REPORT_QUERY, {
            "lat": lat,
            "lon": lng
        })
        
        rows = result.fetchall()
        
    except Exception as e:
        print(f"Error retrieving zone data: {str(e)}")
        return HTTPException(status_code=500, detail=str(e))
    
    if not rows:
        #TODO nearest airports
        res = await nearest_airport(lat, lng, elev, db)
    
    report = []
    
    for r in rows:
        zone = r[0]
        name = r[1]
        air_type = r[2]
        radio = r[3]
        air_elev = r[4]
        distance_m = float(r[5])
        feasibility = "N/A"
        note = "N/A"
        min_height = "N/A"
        
        if zone in ("funnel", "inner"):
            feasibility = "Not Feasible"
            note = f"No WTGs allowed in {zone} zone."
            min_height = "Restricted"
        elif zone == "middle":
            feasibility = "Limited Feasibility"
            note = f"Feasibility limited in middle zone. Based on distance and minimum height"
            mh = calc_min_height(elev, air_elev, distance_m)
            min_height = f"{mh:.1f}m"
        elif zone == "outer":
            feasibility = "Feasible"
            note = f"Feasibile in outer zone but still require NOC for most cases"
            min_height = "Not Required"
            
        report.append({
            "zone": zone,
            "name": name,
            "type": air_type,
            "radio": radio,
            "airport_elevation": air_elev,
            "min_height": min_height,
            "note": note,
            "feasibility": feasibility
        })
            
    return JSONResponse(content=report)

def calc_min_height(elev:float, air_elev:float, distance_m:float):
    
    air_elev = float(air_elev)

    mh = min(air_elev + (45 + 0.05 * (distance_m - 4000)) - elev, 300)
    return mh

async def nearest_airport(lat: float, lng: float, elev: float = 0, db: AsyncSession = None):
    try:
        result = await db.execute(NEAREST_QUERY, {
            "lat": lat,
            "lon": lng
        })
        
        row = result.fetchall()
        
    except Exception as e:
        return HTTPException(status_code=500, detail=str(e))
    
    report = []
    r = row[0]
    zone = "nearest"
    name = r[1]
    air_type = r[2]
    radio = r[3]
    air_elev = r[4]
    distance_m = float(r[5])
    feasibility = "Feasible"
    note = "N/A"
    min_height = "Not Required"
    
    report.append({
            "zone": zone,
            "name": name,
            "type": air_type,
            "radio": radio,
            "airport_elevation": air_elev,
            "min_height": min_height,
            "note": note,
            "feasibility": feasibility
        })
    
    print(report)
        
    return JSONResponse(report)