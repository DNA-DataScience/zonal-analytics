from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import Depends, HTTPException
from fastapi.responses import JSONResponse

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
                               z.aiport_point::geography
                            ) AS distance_m
                    FROM "GisDB".airport_layers z
                    JOIN p
                        ON z.geom3857 && p.geom3857
                        AND ST_Intersects(z.geom3857, p.geom3857);                  
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
        return False
    
    report = []
    
    for r in rows:
        zone = r[0]
        name = r[1]
        air_type = r[2]
        radio = r[3]
        air_elev = r[4]
        distance_m = float(r[5])
        feasibility = ""
        note = ""
        min_height = "N/A"
        
        if air_type in ("funnel", "inner"):
            feasibility = "Not Feasible"
            note = f"No WTGs allowed in {air_type} zone."
            min_height = "Restricted"
        elif air_type == "middle":
            feasibility = "Limited Feasibility"
            note = f"Feasibility limited in middle zone. Based on distance and minimum height"
            min_height = f"Some m"
        elif air_type == "outer":
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